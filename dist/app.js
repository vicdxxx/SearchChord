"use strict";
const methods=[['chord','ChordEdit'],['textsim','SearchChord · TextSim'],['cascade','SearchChord · TextSim → EditReward']];
const roles=[['source','Source'],...methods];
const metricKeys=['psnr_unedit','mse_unedit_x1e3','lpips_unedit_x1e3','clip_whole','clip_edited'];
const esc=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const num=value=>Number(value).toFixed(2);
let data=null,dataset='PIE',activeExample=null,activeRole='cascade';
const dialog=document.querySelector('#image-dialog');
function metricRows(group,family=''){
  const best=metricKeys.map((key,i)=>(i===1||i===2?Math.min:Math.max)(...methods.map(([m])=>group[m][key])));
  return methods.map(([m,label],index)=>`<tr class="${family&&index===0?'family-start':''}">${family?`<td class="family">${index===0?esc(family):''}</td>`:''}<td class="method-name">${esc(label)}</td>${metricKeys.map((key,i)=>`<td class="${num(group[m][key])===num(best[i])?'winner':''}">${num(group[m][key])}</td>`).join('')}</tr>`).join('');
}
function renderTables(){
  document.querySelector('#pie-table tbody').innerHTML=metricRows(data.benchmarks.PIE.all);
  document.querySelector('#crop-table tbody').innerHTML=[['weather','Lighting / weather'],['soil_type','Soil appearance'],['leaf_amount','Relative leaf amount']].map(([key,label])=>metricRows(data.benchmarks.CropWeed.groups[key],label)).join('');
}
function renderCategories(){
  const options=[...new Set(data.examples.filter(e=>e.dataset===dataset).map(e=>e.category))];
  document.querySelector('#category-filter').innerHTML='<option value="">All edit types</option>'+options.map(x=>`<option>${esc(x)}</option>`).join('');
}
function renderGallery(){
  const category=document.querySelector('#category-filter').value;
  const search=document.querySelector('#search').value.trim().toLowerCase();
  const examples=data.examples.filter(e=>e.dataset===dataset&&(!category||category===e.category)&&(!search||[e.title,e.instruction,e.id,e.sourcePrompt,e.targetPrompt].join(' ').toLowerCase().includes(search)));
  document.querySelector('#gallery-count').textContent=`${examples.length} ${dataset==='PIE'?'PIE-Bench':'CropWeed'} comparison${examples.length===1?'':'s'}`;
  document.querySelector('#gallery').innerHTML=examples.length?examples.map((e,index)=>`<article class="example"><header class="example-heading"><div><h3>${esc(e.title)}</h3><p>${esc(e.category)} · ${esc(e.id)}</p></div><span class="example-number" aria-hidden="true">${String(index+1).padStart(2,'0')}</span></header><div class="image-grid">${roles.map(([role,label])=>`<figure><button type="button" class="image-button" data-example="${esc(e.id)}" data-role="${role}" aria-label="Inspect ${esc(label)} image for ${esc(e.title)}"><img src="${esc(e.images[role])}" alt="${esc(label)}: ${esc(e.instruction)}" loading="lazy" decoding="async" width="512" height="512"></button><figcaption>${esc(label)}</figcaption></figure>`).join('')}</div><div class="gain-strip"><span>EditReward cascade vs. ChordEdit</span><span>PSNR <strong>+${num(e.delta.psnr_unedit)} dB</strong></span><span>LPIPS × 10³ <strong>${num(e.delta.lpips_unedit_x1e3)}</strong></span><span>CLIP-Edited <strong>+${num(e.delta.clip_edited)}</strong></span></div><details><summary>Saved scores and full prompts</summary><div class="prompt-pair"><p><strong>Source prompt</strong>${esc(e.sourcePrompt)}</p><p><strong>Target prompt</strong>${esc(e.targetPrompt)}</p></div><div class="table-scroll"><table class="metric-table"><thead><tr><th>Method</th><th>PSNR ↑</th><th>MSE × 10³ ↓</th><th>LPIPS × 10³ ↓</th><th>CLIP-Whole ↑</th><th>CLIP-Edited ↑</th></tr></thead><tbody>${metricRows(e.metrics)}</tbody></table></div></details></article>`).join(''):'<p class="empty-message">No matching edits. Try another search or edit type.</p>';
}
function showRole(role){
  activeRole=role;
  const label=roles.find(([key])=>key===role)[1];
  document.querySelector('#viewer-image').src=activeExample.images[role];
  document.querySelector('#viewer-image').alt=`${label}: ${activeExample.instruction}`;
  document.querySelector('#viewer-prompt').textContent=`${label} · ${role==='source'?activeExample.sourcePrompt:activeExample.targetPrompt}`;
  document.querySelectorAll('.viewer-tabs button').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.role===role)));
}
document.querySelector('#gallery').addEventListener('click',event=>{
  const button=event.target.closest('.image-button');if(!button)return;
  activeExample=data.examples.find(e=>e.id===button.dataset.example&&e.dataset===dataset);
  document.querySelector('#dialog-meta').textContent=`${activeExample.dataset} · ${activeExample.id}`;
  document.querySelector('#dialog-title').textContent=activeExample.instruction;
  showRole(button.dataset.role);dialog.showModal();document.body.classList.add('dialog-open');
});
document.querySelector('#close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('close',()=>document.body.classList.remove('dialog-open'));
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
document.querySelectorAll('.viewer-tabs button').forEach(button=>button.addEventListener('click',()=>showRole(button.dataset.role)));
document.querySelectorAll('.dataset-tabs button').forEach(button=>button.addEventListener('click',()=>{
  if(!data)return;dataset=button.dataset.dataset;document.querySelectorAll('.dataset-tabs button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));document.querySelector('#search').value='';renderCategories();renderGallery();
}));
document.querySelector('#category-filter').addEventListener('change',()=>{if(data)renderGallery();});
document.querySelector('#search').addEventListener('input',()=>{if(data)renderGallery();});
document.querySelector('#copy-citation').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(document.querySelector('#bibtex').textContent);document.querySelector('#citation-status').textContent='BibTeX copied.';}
  catch{const selection=window.getSelection();const range=document.createRange();range.selectNodeContents(document.querySelector('#bibtex'));selection.removeAllRanges();selection.addRange(range);document.querySelector('#citation-status').textContent='Citation selected. Use your browser’s copy command.';}
});
const config=window.SEARCHCHORD_CONFIG||{};
if(config.repositoryUrl){document.querySelectorAll('.repository-link').forEach(link=>{link.href=config.repositoryUrl;link.hidden=false;});}
if(config.siteUrl){document.querySelector('#bibtex').textContent=document.querySelector('#bibtex').textContent.replace('  note = {Research manuscript}','  note = {Research manuscript},\n  url = {'+config.siteUrl+'}');}
fetch('assets/data/results.json').then(response=>{if(!response.ok)throw new Error('Missing results');return response.json();}).then(payload=>{data=payload;document.querySelector('#abstract-copy').textContent=payload.abstract;renderTables();renderCategories();renderGallery();}).catch(()=>{document.querySelector('#gallery-count').textContent='Saved comparisons could not be loaded. Please reload the page.';});
