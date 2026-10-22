import { CHECKCODE_RESULTS as evidence } from './data/checkcode_results.js';
import { renderQueryFrontpage } from './query_frontpage.js';
import { QUERY_VALUE_MODEL, queryCommercialSnapshot } from './query_value.js';

const colors = { blue: '#405bdd', teal: '#078579', gray: '#a1aab9', amber: '#cf9335', dark: '#243750' };
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = (v, digits = 4) => Number.isFinite(Number(v)) ? Number(v).toFixed(digits) : '—';
const int = v => Number(v).toLocaleString('en-US');
const pill = (label, kind = 'measured') => `<span class="pill ${kind}">${esc(label)}</span>`;
const stat = (label, value, detail = '', cls = '') => `<div class="stat"><span class="label">${label}</span><strong class="${cls}">${value}</strong><span class="detail">${detail}</span></div>`;
const options = (entries, selected) => entries.map(([value, label]) => `<option value="${esc(value)}" ${String(value) === String(selected) ? 'selected' : ''}>${esc(label)}</option>`).join('');
const control = (id, label, entries, selected) => `<div class="control"><label for="${id}">${label}</label><select id="${id}">${options(entries, selected)}</select></div>`;
let svgId = 0;

function bars(rows, {min = 0, max = 1, caption = 'Score; higher is better'} = {}) {
  const compact=globalThis.innerWidth<560;
  const left = compact?120:157, right = compact?285:572, width=compact?350:635;
  const top = 18, step = 43, bottom = top + rows.length * step + 7;
  const x = v => left + (Math.max(min, Math.min(max, v)) - min) / (max - min) * (right - left);
  const id = `hatch-${++svgId}`;
  let body = `<defs><pattern id="${id}" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><rect width="5" height="5" fill="#fff2dc"/><path d="M0 0V5" stroke="#d5a354" stroke-width="2"/></pattern></defs>`;
  for (let tick = 0; tick <= 4; tick++) {
    const v = min + (max-min)*tick/4;
    body += `<line class="axis" x1="${x(v)}" x2="${x(v)}" y1="8" y2="${bottom}"/><text x="${x(v)}" y="${bottom+19}" text-anchor="middle">${num(v, 2)}</text>`;
  }
  rows.forEach((row, i) => {
    const y = top+i*step;
    const zero = x(0), end = x(row.value);
    const fill = row.theory ? `url(#${id})` : row.color || colors.blue;
    const label=row.label;
    body += `<text class="label" x="0" y="${y+17}">${esc(label)}</text><rect x="${Math.min(zero,end)}" y="${y}" width="${Math.max(1,Math.abs(end-zero))}" height="24" rx="3" fill="${fill}" ${row.theory ? 'stroke="#c99849" stroke-dasharray="3 2"' : ''}/>`;
    if (row.se) {
      const lo=x(row.value-1.96*row.se), hi=x(row.value+1.96*row.se);
      body += `<path d="M${lo},${y+7}V${y+17}M${lo},${y+12}H${hi}M${hi},${y+7}V${y+17}" stroke="#23354f" stroke-width="1.2"/>`;
    }
    const valueEnd=x(row.value+(row.se?1.96*row.se:0));
    body += `<text class="value" x="${Math.min(right+13, valueEnd+9)}" y="${y+17}">${num(row.value)}</text>`;
  });
  return `<svg class="chart" role="img" aria-label="${esc(caption + ': ' + rows.map(r=>r.label+' '+num(r.value)).join(', '))}" viewBox="0 0 ${width} ${bottom+35}">${body}</svg>`;
}

function download(name, value) {
  const text=JSON.stringify(value,null,2);
  // Qollab exposes sendFile; native browsers use the same downloadable content.
  if (typeof globalThis.sendFile === 'function') {
    globalThis.sendFile(name, 'application/json', text);
    return;
  }
  const url=URL.createObjectURL(new Blob([text],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}

export function mountDashboard(bridge) {
  const state={status:'starting',checkcodeIndex:0,checkcodeLive:null,queryScenario:undefined,
    queryAuditOpen:false,runningTask:'checkcode',shots:512,error:'',info:null};
  const view=document.getElementById('view');
  const bind=(id,event,fn)=>document.getElementById(id)?.addEventListener(event,fn);
  const status=(text,kind)=>{
    const badge=document.getElementById('top-status');
    badge.textContent=text;badge.className='pill '+kind;
  };
  const render=()=>renderQueryFrontpage({state,view,render,run,
    helpers:{pill,stat,int,num,control,bars,download,bind,esc}});
  async function run() {
    if(state.status==='running')return;
    state.status='running';state.error='';state.checkcodeLive=null;
    status('Live job running','neutral');render();
    try {
      state.info=await bridge.info();
      if(!state.info.live_supported) {
        state.status='blocked';state.error=state.info.reason;
        status('Saved evidence ready','neutral');
      } else {
        const result=await bridge.execute(state.shots);
        const q=result?.quantum;
        if(!result?.complete||result.kind!=='live_checkcode'||result.native_backend_calls!==1||
          !q?.quantum_execution||q.shots!==state.shots||
          Object.values(q.raw_counts||{}).reduce((a,b)=>a+b,0)!==q.shots)
          throw new Error('Backend returned an incomplete DQI record. No live result accepted.');
        state.checkcodeLive=result;state.status='done';status('Live job complete','live');
      }
    } catch(error) {
      state.status='failed';state.error=String(error.message||error);status('Live job failed','error');
    } finally {render();}
  }
  bind('export-evidence','click',()=>download('dqi-project-evidence.json',{
    checkcode:evidence,checkcode_live_run:state.checkcodeLive,
    commercial_scenario:queryCommercialSnapshot(state.queryScenario),
    scope:'Saved native DQI evidence, separately identified live execution and explicit scenario projections'
  }));
  document.getElementById('provenance-content').innerHTML=
    '<p class="small-copy">The saved bank contains all 65,536 native outputs from 16 held-out fixtures. Project Run creates a separately labelled 512-shot replay. Scenario exports retain their assumptions and source links.</p>'+
    '<div class="hash-row"><span>Upload evidence SHA-256</span><code>'+QUERY_VALUE_MODEL.measured_evidence_sha256+'</code></div>'+
    '<div class="hash-row"><span>Original audit evidence SHA-256</span><code>'+QUERY_VALUE_MODEL.audited_evidence_sha256+'</code></div>'+
    Object.entries(evidence.source_hashes).map(([name,hash])=>
      '<div class="hash-row"><span>'+esc(name)+'</span><code>'+hash+'</code></div>').join('')+
    '<p class="table-foot"><a href="./CIRCUITS.md#verification-and-reproducibility">Circuit verification and reproducibility</a> · <a href="./README.md#what-is-live-and-what-is-modeled">Data interpretation</a></p>';
  let compact=globalThis.innerWidth<560;
  globalThis.addEventListener('resize',()=>{const next=globalThis.innerWidth<560;if(next!==compact){compact=next;render();}});
  const app={run,state,evidence,refresh:render};
  globalThis.dqiApp=app;render();return app;
}
