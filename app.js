'use strict';
const $=id=>document.getElementById(id);
let config,example,result;
const pct=v=>(100*v).toFixed(2)+'%';
const element=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;};
function status(text,error=false){$('status').textContent=text;$('status').className=error?'error':'';}
function clear(){result=null;$('export').disabled=true;$('metrics').replaceChildren();$('table').replaceChildren();$('chartBox').hidden=true;$('details').textContent='No current result.';$('dataset').textContent='Inputs changed. Run again to update results.';}
function render(output){
  result=output;$('export').disabled=false;$('dataset').textContent=output.dataset_label;
  $('metrics').replaceChildren();
  for(const [key,value] of Object.entries(output.metrics)){
    const card=element('div','');card.className='metric';card.append(element('span',key),element('strong',config.kind==='stock'?pct(value):Number(value).toFixed(key.includes('MAE')?2:0)));$('metrics').append(card);
  }
  const table=element('table',''),thead=element('thead',''),tr=element('tr','');
  const keys=Object.keys(output.rows[0]||{});for(const key of keys)tr.append(element('th',key.replaceAll('_',' ')));thead.append(tr);table.append(thead);
  const body=element('tbody','');for(const row of output.rows){const r=element('tr','');for(const key of keys){const v=row[key];r.append(element('td',typeof v==='number'?(key.includes('probability')||key.includes('return')||key.includes('standard_error')?pct(v):Number.isInteger(v)?String(v):v.toFixed(3)):String(v)));}body.append(r);}table.append(body);$('table').replaceChildren(table);
  $('details').textContent=JSON.stringify(output.details,null,2);
  $('chartBox').hidden=config.kind!=='stock';if(config.kind==='stock')draw(output.series);
}
function draw(series){
  const svg=$('chart');svg.replaceChildren();const all=Object.values(series).flat();const low=Math.min(0,...all),high=Math.max(0,...all);const span=high-low||1;const ns='http://www.w3.org/2000/svg';
  const make=(tag,attrs)=>{const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);svg.append(e);return e;};
  for(let i=0;i<5;i++){const y=20+i*50;make('line',{x1:55,y1:y,x2:790,y2:y,stroke:'#303b43'});make('text',{x:0,y:y+4,fill:'#a8b4bd','font-size':11}).textContent=pct(high-i/4*span);}
  Object.entries(series).forEach(([name,values],i)=>{const points=values.map((v,j)=>`${55+j/(values.length-1||1)*735},${20+(high-v)/span*200}`).join(' ');make('polyline',{points,fill:'none',stroke:i?'#b099ff':'#c4f278','stroke-width':1.8});});
  make('text',{x:55,y:247,fill:'#a8b4bd','font-size':11}).textContent='First held-out observation';make('text',{x:665,y:247,fill:'#a8b4bd','font-size':11}).textContent='Latest observation';
  $('chartSummary').textContent=`${Object.values(series)[0].length} held-out observations. Each prediction uses only earlier data. Exact values are available in the table and JSON export.`;
}
$('run').onclick=async()=>{clear();$('run').disabled=true;status('Training and evaluating…');try{const payload=JSON.parse($('data').value);const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const output=await response.json();if(!response.ok)throw Error(output.error);render(output);status('Analysis complete. Results use the current input.');}catch(e){status(e.message,true);}finally{$('run').disabled=false;}};
$('reset').onclick=()=>{$('data').value=JSON.stringify(example,null,2);clear();status('Historical dataset restored.');};
$('data').oninput=clear;
$('file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>1000000)throw Error('File must be smaller than 1 MB');const data=JSON.parse(await file.text());$('data').value=JSON.stringify(data,null,2);clear();status('File loaded. Run analysis to evaluate it.');}catch(error){status(error.message,true);}e.target.value='';};
$('export').onclick=()=>{if(!result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=config.kind+'-results.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
Promise.all([fetch('/config.json').then(r=>r.json()),fetch('/example.json').then(r=>r.json())]).then(([c,e])=>{config=c;example=e;document.title=c.brand+' — '+c.title;$('brand').textContent=c.brand;$('title').textContent=c.title;$('subtitle').textContent=c.subtitle;$('month').textContent=c.original_completion;$('data').value=JSON.stringify(e,null,2);$('inputHelp').textContent=c.kind==='f1'?'Earlier race results, historical cutoff and target entrants. Features are derived strictly from preceding races.':'80–1,500 dated closing prices, oldest to newest, with an explicit historical cutoff.';$('tableTitle').textContent=c.kind==='f1'?'Simulated finishing outlook':'Walk-forward predictions';status('Historical dataset ready.');}).catch(e=>status('Unable to load example: '+e.message,true));
