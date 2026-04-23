import json

with open(r'C:\Users\weslei\sifilis-duquecaxias\dados_merged.json', encoding='utf-8') as f:
    js_data = f.read()

html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sífilis RJ — SINAN / DATASUS</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Segoe UI',sans-serif; background:#0f172a; color:#e2e8f0; min-height:100vh; }
header { background:linear-gradient(135deg,#1e3a5f,#0f172a); border-bottom:1px solid #334155; padding:20px 28px; }
header h1 { font-size:1.5rem; font-weight:700; color:#f8fafc; }
header p  { color:#94a3b8; font-size:.82rem; margin-top:3px; }
.fonte-badge { display:inline-block; background:#1e40af; color:#bfdbfe; font-size:.7rem; padding:3px 10px; border-radius:20px; margin-top:6px; font-weight:600; }
.search-area { padding:14px 28px; background:#0f172a; border-bottom:1px solid #1e293b; }
.search-wrap { position:relative; max-width:480px; display:inline-block; width:100%; }
.search-wrap input { width:100%; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px 14px 10px 38px; color:#f1f5f9; font-size:.95rem; outline:none; }
.search-wrap input:focus { border-color:#3b82f6; }
.search-wrap .icon { position:absolute; left:11px; top:50%; transform:translateY(-50%); color:#64748b; }
.dropdown { position:absolute; top:calc(100% + 4px); left:0; right:0; background:#1e293b; border:1px solid #334155; border-radius:8px; max-height:280px; overflow-y:auto; z-index:100; display:none; box-shadow:0 8px 24px rgba(0,0,0,.4); }
.dropdown.open { display:block; }
.dropdown-item { padding:9px 14px; cursor:pointer; font-size:.88rem; color:#cbd5e1; border-bottom:1px solid #0f172a; }
.dropdown-item:hover { background:#334155; color:#f8fafc; }
.ibge { color:#475569; font-size:.75rem; margin-left:6px; }
.mun-label { display:inline-block; margin-left:14px; color:#38bdf8; font-size:.88rem; font-weight:600; vertical-align:middle; }
.kpi-row { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; padding:16px 28px 0; }
@media(max-width:800px){ .kpi-row{ grid-template-columns:1fr; } }
.kpi { background:#1e293b; border:1px solid #334155; border-radius:10px; padding:14px 18px; }
.kpi-label { font-size:.7rem; text-transform:uppercase; letter-spacing:.07em; color:#94a3b8; }
.kpi-val { font-size:2rem; font-weight:800; line-height:1.1; }
.kpi-sub { font-size:.72rem; color:#64748b; margin-top:3px; }
.azul{color:#38bdf8;} .rosa{color:#f472b6;} .verde{color:#34d399;} .laranja{color:#fb923c;} .cinza{color:#64748b;}
.sec { padding:14px 28px 6px; font-size:.75rem; text-transform:uppercase; letter-spacing:.1em; color:#475569; font-weight:700; border-top:1px solid #1e293b; margin-top:4px; }
.g3 { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; padding:0 28px 14px; }
.g4 { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; padding:0 28px 14px; }
.g2 { display:grid; grid-template-columns:repeat(2,1fr); gap:14px; padding:0 28px 14px; }
@media(max-width:900px){ .g3,.g4,.g2{ grid-template-columns:1fr; } }
.cc { background:#1e293b; border:1px solid #334155; border-radius:10px; padding:16px; }
.ct { font-size:.84rem; font-weight:600; color:#cbd5e1; margin-bottom:12px; }
.cw { position:relative; height:190px; }
.cw.t { height:220px; }
.sp2 { grid-column:span 2; }
.sp3 { grid-column:span 3; }
@media(max-width:900px){ .sp2,.sp3{ grid-column:span 1; } }
.tw { overflow-x:auto; padding:0 28px 14px; }
table { width:100%; border-collapse:collapse; font-size:.79rem; }
th { background:#0f172a; color:#94a3b8; padding:7px 10px; text-align:center; font-size:.7rem; text-transform:uppercase; }
td { padding:7px 10px; text-align:center; border-bottom:1px solid #0f172a; }
tr:nth-child(even) td { background:#1a2744; }
td.l { text-align:left; color:#cbd5e1; font-weight:500; }
td.b { font-weight:700; background:#0f172a !important; }
footer { text-align:center; padding:18px 28px; font-size:.7rem; color:#475569; border-top:1px solid #1e293b; margin-top:4px; }
footer a { color:#3b82f6; text-decoration:none; }
.nd { color:#ef4444; font-size:.82rem; padding:24px 28px; }
</style>
</head>
<body>
<header>
  <h1>Sífilis — Estado do Rio de Janeiro</h1>
  <p>Notificações registradas no SINAN · 2017–2024 · Município de residência</p>
  <span class="fonte-badge">SINAN / DATASUS — dados oficiais</span>
</header>
<div class="search-area">
  <div class="search-wrap">
    <span class="icon">&#128269;</span>
    <input type="text" id="si" placeholder="Buscar município (ex: Caxias, Niterói, Rio...)" autocomplete="off">
    <div class="dropdown" id="dd"></div>
  </div>
  <span class="mun-label" id="ml">— selecione um município —</span>
</div>
<div id="mc" style="display:none">
  <div class="kpi-row">
    <div class="kpi"><div class="kpi-label">Sífilis Adquirida</div><div class="kpi-val azul" id="ka">—</div><div class="kpi-sub">notificações · 2017–2024</div></div>
    <div class="kpi"><div class="kpi-label">Sífilis Congênita</div><div class="kpi-val rosa" id="kc">—</div><div class="kpi-sub">casos confirmados · 2017–2024</div></div>
    <div class="kpi"><div class="kpi-label">Sífilis em Gestante</div><div class="kpi-val verde" id="kg">—</div><div class="kpi-sub">notificações · 2017–2024</div></div>
  </div>
  <div class="sec">Série Histórica 2017–2024</div>
  <div class="g3">
    <div class="cc"><div class="ct">Adquirida · por ano</div><div class="cw"><canvas id="cA"></canvas></div></div>
    <div class="cc"><div class="ct">Congênita · por ano</div><div class="cw"><canvas id="cC"></canvas></div></div>
    <div class="cc"><div class="ct">Gestante · por ano</div><div class="cw"><canvas id="cG"></canvas></div></div>
  </div>
  <div class="g3">
    <div class="cc sp3"><div class="ct">Evolução comparativa 2017–2023</div><div class="cw t"><canvas id="cL"></canvas></div></div>
  </div>
  <div class="sec">Perfil Demográfico — Adquirida</div>
  <div class="g4">
    <div class="cc"><div class="ct">Por Sexo</div><div class="cw"><canvas id="dAs"></canvas></div></div>
    <div class="cc"><div class="ct">Por Raça/Cor</div><div class="cw"><canvas id="dAr"></canvas></div></div>
    <div class="cc"><div class="ct">Classificação</div><div class="cw"><canvas id="dAc"></canvas></div></div>
    <div class="cc"><div class="ct">Faixa Etária</div><div class="cw"><canvas id="dAf"></canvas></div></div>
  </div>
  <div class="sec">Perfil Demográfico — Congênita &amp; Gestante</div>
  <div class="g3">
    <div class="cc"><div class="ct">Congênita · Evolução</div><div class="cw"><canvas id="dCe"></canvas></div></div>
    <div class="cc"><div class="ct">Gestante · Faixa Etária</div><div class="cw"><canvas id="dGf"></canvas></div></div>
    <div class="cc"><div class="ct">Congênita · Faixa Etária</div><div class="cw"><canvas id="dCf"></canvas></div></div>
  </div>
  <div class="sec">Série Histórica Completa</div>
  <div class="tw">
    <table>
      <thead><tr><th>Tipo</th><th>2017</th><th>2018</th><th>2019</th><th>2020</th><th>2021</th><th>2022</th><th>2023</th><th>2024*</th><th>Total</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
    <p style="font-size:.68rem;color:#475569;margin-top:8px;">* 2024: dados parciais. Fonte: <a href="http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sinannet/cnv/SifilisAdquiridaRJ.def" target="_blank">SINAN Adquirida</a> · <a href="http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sinannet/cnv/sifilisRJ.def" target="_blank">Congênita</a> · <a href="http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sinannet/cnv/SifilisGestanteRJ.def" target="_blank">Gestante</a></p>
  </div>
</div>
<div id="nd" style="display:none"><p class="nd">Nenhum dado encontrado para este município no período 2017–2024.</p></div>
<footer>
  Fonte: Ministério da Saúde / SVSA — SINAN via DATASUS Tabnet · RJ · 92 municípios · Abril/2026
</footer>
<script>
const D=__DADOS__;
const ANOS=['2017','2018','2019','2020','2021','2022','2023','2024*'];
const A7=['2017','2018','2019','2020','2021','2022','2023'];
const LISTA=Object.entries(D).map(([i,d])=>({i,n:d.nome})).sort((a,b)=>a.n.localeCompare(b.n));
const CO={az:'#38bdf8',ro:'#f472b6',ve:'#34d399',la:'#fb923c',rx:'#a78bfa',ci:'#64748b',am:'#fbbf24',vm:'#f87171'};
const AX={grid:{color:'#1e293b'},ticks:{color:'#94a3b8',font:{size:10}}};
let CH={};
function mk(id){if(CH[id])CH[id].destroy();return id;}
function bar(id,lb,dt,c){CH[id]=new Chart(document.getElementById(mk(id)),{type:'bar',data:{labels:lb,datasets:[{data:dt,backgroundColor:c+'55',borderColor:c,borderWidth:1,borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:AX,y:{...AX,beginAtZero:true}}}});}
function hb(id,lb,dt,c){CH[id]=new Chart(document.getElementById(mk(id)),{type:'bar',data:{labels:lb,datasets:[{data:dt,backgroundColor:c+'55',borderColor:c,borderWidth:1,borderRadius:3}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:AX,y:AX}}});}
function dn(id,lb,vl,cs){CH[id]=new Chart(document.getElementById(mk(id)),{type:'doughnut',data:{labels:lb,datasets:[{data:vl,backgroundColor:cs,borderWidth:2,borderColor:'#0f172a'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{color:'#94a3b8',font:{size:10},boxWidth:12}}}}});}
function ln(id,lb,ds){CH[id]=new Chart(document.getElementById(mk(id)),{type:'line',data:{labels:lb,datasets:ds},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,labels:{color:'#cbd5e1',font:{size:11}}}},scales:{x:AX,y:{...AX,beginAtZero:true}}}});}
function fmt(n){return n.toLocaleString('pt-BR');}
function sm(a){return a.reduce((s,v)=>s+v,0);}
function decHtml(s){return s.replace(/&[A-Za-z]+;/g,e=>({'&Oacute;':'Ó','&oacute;':'ó','&Aacute;':'Á','&aacute;':'á','&Eacute;':'É','&eacute;':'é','&Ccedil;':'Ç','&ccedil;':'ç','&atilde;':'ã','&Atilde;':'Ã','&otilde;':'õ'}[e]||e));}

function render(ibge,nome){
  const d=D[ibge];
  document.getElementById('ml').textContent=nome+' ('+ibge+')';
  if(sm(d.adq)+sm(d.cong)+sm(d.gest)===0){
    document.getElementById('mc').style.display='none';
    document.getElementById('nd').style.display='block'; return;
  }
  document.getElementById('nd').style.display='none';
  document.getElementById('mc').style.display='block';
  document.getElementById('ka').textContent=fmt(sm(d.adq));
  document.getElementById('kc').textContent=fmt(sm(d.cong));
  document.getElementById('kg').textContent=fmt(sm(d.gest));
  bar('cA',ANOS,d.adq,CO.az); bar('cC',ANOS,d.cong,CO.ro); bar('cG',ANOS,d.gest,CO.ve);
  ln('cL',A7,[
    {label:'Adquirida',data:d.adq.slice(0,7),borderColor:CO.az,backgroundColor:CO.az+'15',fill:true,tension:.3,pointRadius:4},
    {label:'Gestante', data:d.gest.slice(0,7),borderColor:CO.ve,backgroundColor:CO.ve+'15',fill:true,tension:.3,pointRadius:4},
    {label:'Congênita',data:d.cong.slice(0,7),borderColor:CO.ro,backgroundColor:CO.ro+'15',fill:true,tension:.3,pointRadius:4},
  ]);
  // table
  const tb=document.getElementById('tb');
  tb.innerHTML=[{l:'Adquirida',c:'azul',v:d.adq},{l:'Congênita',c:'rosa',v:d.cong},{l:'Gestante',c:'verde',v:d.gest}]
    .map(r=>`<tr><td class="l ${r.c}">${r.l}</td>${r.v.map(x=>`<td class="${r.c}">${x||'—'}</td>`).join('')}<td class="b ${r.c}">${fmt(sm(r.v))}</td></tr>`).join('');
  // demo
  const dm=d.demo||{};
  const sx=dm.adq_sexo||{};
  if(Object.keys(sx).length) dn('dAs',['Masculino','Feminino','Ignorado'],[sx.Masculino||0,sx.Feminino||0,sx.Ignorado||0],[CO.az,CO.ro,CO.ci]);
  const ra=dm.adq_raca||{};
  const rak=Object.keys(ra).filter(k=>k!=='Ign/Branco');
  if(rak.length) dn('dAr',rak,rak.map(k=>ra[k]),[CO.la,CO.az,CO.vm,CO.am,CO.rx,CO.ve]);
  const cl=dm.adq_clas||{};
  const clk=Object.keys(cl);
  if(clk.length) dn('dAc',clk,clk.map(k=>cl[k]),[CO.la,CO.ve,CO.ci,CO.az]);
  const af=dm.adq_fxet||{};
  const afk=Object.keys(af).filter(k=>k!=='Em branco/IGN');
  if(afk.length) hb('dAf',afk,afk.map(k=>af[k]),CO.az);
  const ce=dm.cong_evol||{};
  const cek=Object.keys(ce);
  if(cek.length) dn('dCe',cek.map(decHtml),cek.map(k=>ce[k]),[CO.ve,CO.vm,CO.ci,CO.la]);
  const gf=dm.gest_fxet||{};
  const gfk=Object.keys(gf);
  if(gfk.length) hb('dGf',gfk,gfk.map(k=>gf[k]),CO.ve);
  const cf=dm.cong_fxet||{};
  const cfk=Object.keys(cf);
  if(cfk.length) hb('dCf',cfk,cfk.map(k=>cf[k]),CO.ro);
}

const inp=document.getElementById('si'),dd=document.getElementById('dd');
function norm(s){return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toUpperCase();}
inp.addEventListener('input',()=>{
  const q=norm(inp.value.trim());
  if(!q){dd.classList.remove('open');return;}
  const h=LISTA.filter(m=>norm(m.n).includes(q)).slice(0,12);
  if(!h.length){dd.classList.remove('open');return;}
  dd.innerHTML=h.map(m=>`<div class="dropdown-item" onclick="pick('${m.i}','${m.n}')">${m.n}<span class="ibge">${m.i}</span></div>`).join('');
  dd.classList.add('open');
});
inp.addEventListener('blur',()=>setTimeout(()=>dd.classList.remove('open'),200));
function pick(i,n){dd.classList.remove('open');inp.value=n;render(i,n);}
window.addEventListener('DOMContentLoaded',()=>pick('330170','DUQUE DE CAXIAS'));
</script>
</body>
</html>"""

html = html.replace('__DADOS__', js_data)

with open(r'C:\Users\weslei\sifilis-duquecaxias\index.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"OK — {len(html)/1024:.0f} KB")
