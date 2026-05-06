#!/usr/bin/env python3
"""
fetch_dc_18_29.py
Tenta puxar do SINAN/Tabnet os casos de sifilis adquirida em
Duque de Caxias (IBGE 330170) por faixa etaria granular,
filtrando exclusivamente o municipio.

Estrategia:
  Linha   = Faixa Etaria (mais granular disponivel)
  Coluna  = Ano de diagnostico
  Filtro  = Municipio_resid contem '330170'
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fetch_datasus import (
    SESS, BASE, DEFS, get_form, parse_select_opts, parse_arquivos,
    find_opt, _enc, parse_prn, decode_ents
)
import re, json, time

def list_form_options(def_path):
    print(f"\n=== Form: {def_path} ===")
    html = get_form(def_path)
    linha  = parse_select_opts(html, 'Linha')
    coluna = parse_select_opts(html, 'Coluna')
    incr   = parse_select_opts(html, 'Incremento')
    print("\nLinha (rows) options:")
    for k in linha: print(f"  - {k!r}")
    print("\nColuna (cols) options:")
    for k in coluna: print(f"  - {k!r}")
    print("\nIncremento options:")
    for k in incr: print(f"  - {k!r}")
    # tambem listar campos de filtro (Selecoes Disponiveis)
    print("\nCampos de filtro (selectables):")
    sel_blocks = re.findall(r'<select[^>]+name=["\']?(S\w+)["\']?', html, re.I)
    print(f"  {sel_blocks}")
    return html, linha, coluna, incr

def post_with_filter(def_path, linha_val, coluna_val, incr_val, arquivos,
                    filter_field, filter_value, retries=3):
    """POST com filtro adicional (ex: SMunic_Res = '330170 Duque de Caxias')."""
    data = [
        ('Linha',      _enc(linha_val)),
        ('Coluna',     _enc(coluna_val)),
        ('Incremento', _enc(incr_val)),
        ('formato',    b'prn'),
        ('mostre',     b'Mostra'),
        (filter_field, _enc(filter_value)),
    ]
    for arq in arquivos:
        data.append(('Arquivos', _enc(arq)))

    url = f"{BASE}?{def_path}"
    for attempt in range(retries):
        try:
            r = SESS.post(url, data=data, timeout=120)
            r.raise_for_status()
            html = r.content.decode('iso-8859-1', errors='replace')
            return parse_prn(html), html
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise

def find_municipio_value(html, ibge_target='330170', prefer='resid'):
    """Procura o option do municipio no select de filtro com codigo IBGE.
    prefer='resid' prioriza Municipio_de_residencia, 'notif' prioriza notificacao."""
    selects = re.findall(
        r'<select[^>]+name=["\']?(S\w*[Mm]unic\w*)["\']?[^>]*>(.*?)</select>',
        html, re.S | re.I
    )
    # Reordena para priorizar residencia (decoded chars: 'resid' aparece em label)
    def score(name):
        n = decode_ents(name).lower()
        if prefer == 'resid' and 'resid' in n: return 0
        if prefer == 'notif' and 'notif' in n: return 0
        if 'resid' in n: return 1
        if 'notif' in n: return 2
        return 3
    selects.sort(key=lambda x: score(x[0]))
    for name, body in selects:
        opts = re.findall(
            r'<option[^>]+value=["\']([^"\']*)["\'][^>]*>\s*([^<\r\n]+)',
            body, re.I
        )
        for val, label in opts:
            label_clean = decode_ents(label).strip()
            if ibge_target in val or ibge_target in label_clean:
                return name, val, label_clean
    return None, None, None

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    def_path = DEFS['adq']

    html, linha, coluna, incr = list_form_options(def_path)

    # Acha campo de filtro de municipio
    fname, fval, flabel = find_municipio_value(html, '330170')
    print(f"\nFiltro municipio DC -> field={fname!r} value={fval!r} label={flabel!r}")
    if not fname:
        print("ERRO: nao encontrei option de Duque de Caxias no select de filtro")
        return

    # Procura faixa etaria mais granular
    fxet_candidates = [k for k in linha if 'fa' in k.lower() and 'et' in k.lower()]
    print(f"\nCandidatos faixa etaria em LINHA: {fxet_candidates}")
    if not fxet_candidates:
        print("ERRO: faixa etaria nao disponivel em Linha")
        return

    # Pega a primeira (geralmente ja e a mais granular)
    fxet_label = fxet_candidates[0]
    linha_val = linha[fxet_label]
    coluna_val = (find_opt(coluna, 'ano', 'notif') or
                  find_opt(coluna, 'ano', 'diagn') or
                  find_opt(coluna, 'ano'))
    incr_val = find_opt(incr, 'caso') or next(iter(incr.values()))

    arq_map = parse_arquivos(html)
    arquivos = [arq_map[a] for a in sorted(arq_map.keys()) if 2017 <= a <= 2025]
    print(f"\nUsando: linha={fxet_label!r} coluna={coluna_val!r} arquivos={len(arquivos)}")

    data, _ = post_with_filter(def_path, linha_val, coluna_val, incr_val,
                                arquivos, fname, fval)
    print(f"\n=== Resultado: faixa etaria x ano (filtro DC) ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # Salva
    out = {
        'municipio': 'Duque de Caxias',
        'ibge': '330170',
        'filtro_field': fname,
        'filtro_value': fval,
        'linha': fxet_label,
        'coluna': coluna_val,
        'data': data,
    }
    with open('dc_adq_faixa_etaria.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nSalvo em dc_adq_faixa_etaria.json")

if __name__ == '__main__':
    main()
