'use strict';
// The page selects preserved observations; it never calls an inference provider.
const byId=id=>document.getElementById(id);
async function readData(path){const r=await fetch(path);if(!r.ok)throw new Error('Could not load '+path);return r.json();}
async function setupVideo(){
 const video=byId('seven-video');if(!video)return;
 const manifest=await readData('evidence/demo/manifest.json');
 const times=new Map(manifest.checkpoints.map(c=>[c.label,c.seconds]));
 const buttons=[...document.querySelectorAll('[data-chapter]')],status=byId('video-status');let request=0;
 function showStatus(text){status.textContent=text;status.hidden=!text;}
 function waitFor(event,ready){
  if(video.error||video.networkState===3)return Promise.reject(new Error('Video unavailable'));
  if(ready())return Promise.resolve();
  return new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>done(new Error('Loading timed out')),15000);
   function clean(){clearTimeout(timer);video.removeEventListener(event,success);video.removeEventListener('error',failure,true);}
   function done(error){clean();error?reject(error):resolve();}
   function success(){done();}function failure(){done(new Error('Video unavailable'));}
   video.addEventListener(event,success,{once:true});video.addEventListener('error',failure,{once:true,capture:true});
  });
 }
 for(const button of buttons){
  button.setAttribute('aria-pressed','false');
  button.addEventListener('click',async()=>{
   const current=++request,target=times.get(button.dataset.chapter);
   buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));showStatus('Loading this moment…');
   try{
    const metadata=waitFor('loadedmetadata',()=>video.readyState>=1);
    if(video.readyState===0&&video.networkState!==2){video.preload='auto';video.load();}
    await metadata;
    // Metadata can arrive before a seekable range exists. Seeking at that point
    // can silently clamp the requested chapter to zero (observed in Chrome).
    await waitFor('canplay',()=>video.readyState>=3);
    if(current!==request)return;
    video.pause();video.currentTime=target;
    await waitFor('seeked',()=>!video.seeking);if(current!==request)return;
    await video.play();if(current===request)showStatus('');
   }catch(error){if(current===request)showStatus(error.message==='Video unavailable'?'The recording could not load. Reload the page to try again.':'Use the video’s play control to continue, then choose a moment again.');}
  });
 }
}
async function setupAnswers(){
 const select=byId('answer-select');if(!select)return;
 const records=await readData('data/answers.json');
 for(const [i,r]of records.entries())select.add(new Option(`Question ${i+1} · test row ${r.row}`,String(i)));
 const el=(tag,text,className)=>{const e=document.createElement(tag);e.textContent=text;if(className)e.className=className;return e;};
 function show(index){
  index=(index+records.length)%records.length;select.value=String(index);const record=records[index];
  byId('answer-position').textContent=`Question ${index+1} of ${records.length} · GSM8K test row ${record.row}`;
  byId('answer-question').textContent=record.question;byId('answer-reference').textContent=record.reference;
  byId('answer-columns').replaceChildren(...record.answers.map(a=>{
   const box=document.createElement('section');box.className='answer';
   box.append(el('h3',a.configuration),el('p',`${a.correct?'Numeric match':'No numeric match'} · Uncertainty ${a.would_escalate?'triggered':'not triggered'}`,'answer-grade'),el('blockquote',a.response));return box;
  }));
 }
 select.addEventListener('change',()=>show(Number(select.value)));
 byId('answer-prev').addEventListener('click',()=>show(Number(select.value)-1));byId('answer-next').addEventListener('click',()=>show(Number(select.value)+1));show(0);
}
setupVideo().catch(()=>{const s=byId('video-status');if(s){s.hidden=false;s.textContent='Chapter shortcuts are unavailable. Use the video controls.';}});
setupAnswers().catch(()=>{byId('answer-question').textContent='The responses could not load. Open this page through the local preview server.';});
