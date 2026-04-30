#!/usr/bin/env python3
"""
fetch_datasus.py
Baixa dados de sífilis RJ do DATASUS Tabnet (POST/PRE)
Gera: dados_rj.json, demo_rj.json, dados_merged.json
"""
import requests, re, json, time, sys, unicodedata

BASE = "http://tabnet.datasus.gov.br/cgi/tabcgi.exe"
SESS = requests.Session()
SESS.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
})

DEFS = {
    'adq':  'sinannet/cnv/SifilisAdquiridaRJ.def',
    'cong': 'sinannet/cnv/sifilisRJ.def',
    'gest': 'sinannet/cnv/SifilisGestanteRJ.def',
}

# Anos alvo para o JSON final (2025 = 0 enquanto não publicado)
ANOS_JSON = list(range(2017, 2026))  # 2017-2025

ENTITIES = [
    ('&iacute;','í'),('&Iacute;','Í'),('&eacute;','é'),('&Eacute;','É'),
    ('&aacute;','á'),('&Aacute;','Á'),('&oacute;','ó'),('&Oacute;','Ó'),
    ('&uacute;','ú'),('&Uacute;','Ú'),('&ccedil;','ç'),('&Ccedil;','Ç'),
    ('&atilde;','ã'),('&Atilde;','Ã'),('&otilde;','õ'),('&Otilde;','Õ'),
    ('&ecirc;','ê'),('&Ecirc;','Ê'),('&ocirc;','ô'),('&Ocirc;','Ô'),
    ('&acirc;','â'),('&Acirc;','Â'),('&amp;','&'),('&quot;','"'),('&nbsp;',' '),
]

def decode_ents(s):
    for ent, ch in ENTITIES:
        s = s.replace(ent, ch)
    return s

def norm_name(s):
    """Normaliza nome de município para matching: remove código IBGE, acentos, upper."""
    s = decode_ents(s).upper().strip()
    s = re.sub(r'^\d{6,7}\s*', '', s)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.strip()

def get_form(def_path, retries=3):
    url = f"{BASE}?{def_path}"
    for attempt in range(retries):
        try:
            r = SESS.get(url, timeout=40)
            r.raise_for_status()
            # Força decodificação ISO-8859-1 (charset da página)
            return r.content.decode('iso-8859-1', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise

def parse_select_opts(html, select_name):
    """Extrai options de um select pelo NAME (case-insensitive)."""
    m = re.search(
        rf'<select[^>]+name=["\']?{re.escape(select_name)}["\']?[^>]*>(.*?)</select>',
        html, re.S | re.I
    )
    if not m:
        return {}
    # re.I para pegar <OPTION> maiúsculo
    opts = re.findall(
        r'<option[^>]+value=["\']([^"\']*)["\'][^>]*>\s*([^<\r\n]+)',
        m.group(1), re.I
    )
    # Decodifica entities nos labels para matching correto (ex: Ra&ccedil;a → Raça)
    return {decode_ents(label).strip(): val for val, label in opts if val}

def parse_arquivos(html):
    """Retorna {ano_int: filename} a partir do select Arquivos."""
    opts = parse_select_opts(html, 'Arquivos')
    result = {}
    for label, val in opts.items():
        m = re.search(r'(\d{4})', label)
        if m:
            result[int(m.group(1))] = val
    return result

def find_opt(opts, *keywords):
    for label, val in opts.items():
        lb = label.lower()
        if all(k.lower() in lb for k in keywords):
            return val
    return None

def _enc(s):
    """Codifica string como bytes ISO-8859-1 — Tabnet espera latin-1, não UTF-8."""
    if isinstance(s, str):
        return s.encode('iso-8859-1', errors='replace')
    return s

def post_prn(def_path, linha_val, coluna_val, incr_val, arquivos, retries=3):
    data = [
        ('Linha',      _enc(linha_val)),
        ('Coluna',     _enc(coluna_val)),
        ('Incremento', _enc(incr_val)),
        ('formato',    b'prn'),
        ('mostre',     b'Mostra'),
    ]
    for arq in arquivos:
        data.append(('Arquivos', _enc(arq)))

    url = f"{BASE}?{def_path}"
    for attempt in range(retries):
        try:
            r = SESS.post(url, data=data, timeout=120)
            r.raise_for_status()
            html = r.content.decode('iso-8859-1', errors='replace')
            return parse_prn(html)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise

def parse_prn(html):
    html = decode_ents(html)
    m = re.search(r'<PRE>(.*?)</PRE>', html, re.S | re.I)
    if not m:
        return {}
    lines = [l.strip() for l in m.group(1).strip().split('\n') if l.strip()]
    if len(lines) < 2:
        return {}
    headers = [h.strip('"').strip() for h in lines[0].split(';')]
    result = {}
    for line in lines[1:]:
        cells = [c.strip('"').strip() for c in line.split(';')]
        if not cells or cells[0].strip() in ('Total', 'TOTAL', ''):
            continue
        row = cells[0].strip()
        result[row] = {}
        for i, col in enumerate(headers[1:], 1):
            if i < len(cells):
                v = cells[i].replace('.', '').replace(',', '.')
                try:
                    result[row][col] = int(float(v)) if v.strip() not in ('-', '', '...', '..') else 0
                except Exception:
                    result[row][col] = 0
    return result

def load_existing():
    with open('dados_rj.json', encoding='utf-8') as f:
        d = json.load(f)
    ibge_by_norm = {}
    nome_by_ibge = {}
    for ibge, v in d.items():
        nome_by_ibge[ibge] = v['nome']
        ibge_by_norm[norm_name(v['nome'])] = ibge
    return ibge_by_norm, nome_by_ibge

def fetch_series(ibge_by_norm, nome_by_ibge):
    series = {ibge: {'adq': [0]*len(ANOS_JSON), 'cong': [0]*len(ANOS_JSON), 'gest': [0]*len(ANOS_JSON)}
              for ibge in nome_by_ibge}

    for tipo, def_path in DEFS.items():
        print(f"  Série {tipo}... ", end='', flush=True)
        try:
            form_html = get_form(def_path)
        except Exception as e:
            print(f"ERRO form: {e}")
            continue

        linha_opts  = parse_select_opts(form_html, 'Linha')
        coluna_opts = parse_select_opts(form_html, 'Coluna')
        incr_opts   = parse_select_opts(form_html, 'Incremento')
        arq_map     = parse_arquivos(form_html)

        linha_val = find_opt(linha_opts, 'munic', 'resid')
        coluna_val = (find_opt(coluna_opts, 'ano', 'diagn') or
                      find_opt(coluna_opts, 'ano', 'notif') or
                      find_opt(coluna_opts, 'ano'))
        incr_val  = (find_opt(incr_opts, 'todos') or
                     find_opt(incr_opts, 'caso') or
                     next(iter(incr_opts.values()), 'Todos_os_casos'))

        if not linha_val or not coluna_val:
            print(f"ERRO campos: linha={linha_val} coluna={coluna_val}")
            print(f"    Linha: {list(linha_opts.items())[:3]}")
            print(f"    Coluna: {list(coluna_opts.items())[:3]}")
            continue

        # Seleciona arquivos disponíveis (2017 em diante)
        arquivos = [arq_map[a] for a in sorted(arq_map.keys()) if a >= 2017]
        if not arquivos:
            print(f"ERRO: nenhum arquivo 2017+ encontrado. arq_map={arq_map}")
            continue

        anos_disponiveis = sorted(a for a in arq_map if a >= 2017)
        print(f"anos {anos_disponiveis[0]}-{anos_disponiveis[-1]}... ", end='', flush=True)

        try:
            data = post_prn(def_path, linha_val, coluna_val, incr_val, arquivos)
        except Exception as e:
            print(f"ERRO post: {e}")
            continue

        matched = 0
        unmatched = []
        for raw_mun, cols in data.items():
            nk = norm_name(raw_mun)
            ibge = ibge_by_norm.get(nk)
            if not ibge:
                unmatched.append(raw_mun)
                continue
            matched += 1
            for idx, ano in enumerate(ANOS_JSON):
                ano_str = str(ano)
                series[ibge][tipo][idx] = cols.get(ano_str, 0)

        print(f"OK ({matched}/{len(nome_by_ibge)} municípios)")
        if unmatched:
            print(f"    Não-mapeados ({len(unmatched)}): {unmatched[:5]}")
        if matched == 0 and data:
            primeiros = list(data.items())[:3]
            print(f"    PRN sample: {primeiros}")
        time.sleep(2)

    return series

def fetch_demo(ibge_by_norm, nome_by_ibge):
    demo = {ibge: {} for ibge in nome_by_ibge}

    queries = [
        ('adq',  'sexo',    'adq_sexo'),
        ('adq',  'raça',    'adq_raca'),
        ('adq',  'faixa',   'adq_fxet'),
        ('adq',  'classif', 'adq_clas'),
        ('cong', 'evolu',   'cong_evol'),
        ('cong', 'faixa',   'cong_fxet'),
        ('gest', 'faixa',   'gest_fxet'),
    ]

    for tipo_key, col_kw, demo_field in queries:
        def_path = DEFS[tipo_key]
        print(f"  Demo {demo_field}... ", end='', flush=True)
        try:
            form_html = get_form(def_path)
        except Exception as e:
            print(f"ERRO form: {e}")
            continue

        linha_opts  = parse_select_opts(form_html, 'Linha')
        coluna_opts = parse_select_opts(form_html, 'Coluna')
        incr_opts   = parse_select_opts(form_html, 'Incremento')
        arq_map     = parse_arquivos(form_html)

        linha_val = find_opt(linha_opts, 'munic', 'resid')
        coluna_val = find_opt(coluna_opts, col_kw)
        incr_val  = (find_opt(incr_opts, 'todos') or
                     find_opt(incr_opts, 'caso') or
                     next(iter(incr_opts.values()), 'Todos_os_casos'))

        if not linha_val or not coluna_val:
            print(f"SKIP ('{col_kw}' não encontrado — opts: {list(coluna_opts.keys())[:5]})")
            continue

        arquivos = [arq_map[a] for a in sorted(arq_map.keys()) if a >= 2017]

        try:
            data = post_prn(def_path, linha_val, coluna_val, incr_val, arquivos)
        except Exception as e:
            print(f"ERRO post: {e}")
            continue

        matched = 0
        for raw_mun, cats in data.items():
            nk = norm_name(raw_mun)
            ibge = ibge_by_norm.get(nk)
            if not ibge:
                continue
            matched += 1
            demo[ibge][demo_field] = cats

        print(f"OK ({matched}/{len(nome_by_ibge)})")
        time.sleep(2)

    return demo

def main():
    import os
    os.chdir(r'C:\Users\weslei\sifilis-duquecaxias')

    print("=== fetch_datasus.py — Sífilis RJ ===")

    ibge_by_norm, nome_by_ibge = load_existing()
    print(f"Municípios no mapeamento: {len(nome_by_ibge)}")

    print("\n[1/3] Série histórica (município × ano)...")
    series = fetch_series(ibge_by_norm, nome_by_ibge)

    print("\n[2/3] Perfil demográfico...")
    demo = fetch_demo(ibge_by_norm, nome_by_ibge)

    print("\n[3/3] Salvando JSONs...")

    dados_rj = {}
    for ibge, nome in nome_by_ibge.items():
        dados_rj[ibge] = {
            'nome': nome,
            'adq':  series[ibge]['adq'],
            'cong': series[ibge]['cong'],
            'gest': series[ibge]['gest'],
        }
    with open('dados_rj.json', 'w', encoding='utf-8') as f:
        json.dump(dados_rj, f, ensure_ascii=False)
    print("  dados_rj.json OK")

    with open('demo_rj.json', 'w', encoding='utf-8') as f:
        json.dump(demo, f, ensure_ascii=False)
    print("  demo_rj.json OK")

    dados_merged = {}
    for ibge, entry in dados_rj.items():
        dados_merged[ibge] = {**entry, 'demo': demo.get(ibge, {})}
    with open('dados_merged.json', 'w', encoding='utf-8') as f:
        json.dump(dados_merged, f, ensure_ascii=False)
    print("  dados_merged.json OK")

    print("\nRodando build_index.py...")
    import subprocess
    subprocess.run([sys.executable, 'build_index.py'], check=True)
    print("\nPronto! Faça git commit + push para publicar.")

if __name__ == '__main__':
    main()
