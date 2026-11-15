'use strict';
// The page selects preserved observations; it never calls an inference provider.
const byId=id=>document.getElementById(id);
async function readData(path){const r=await fetch(path);if(!r.ok)throw new Error('Could not load '+path);return r.json();}
async function setupVideo(){
 const video=byId('seven-video');if(!video)return;
 const manifest=await readData('evidence/demo/manifest.json');
 const times=new Map(manifest.checkpoints.map(c=>[c.label,c.seconds]));
 const buttons=[...document.querySelectorAll('[data-chapter]')],status=byId('video-status'),toggle=byId('tour-toggle');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');let request=0,pending=false,wantsPlay=!reduced.matches,selected=null;
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
 function mark(button){selected=button;buttons.forEach(b=>{b.setAttribute('aria-pressed',String(b===button));b.style.setProperty('--progress','0');});}
 function sync(){
  toggle.textContent=(pending?wantsPlay:!video.paused)?'Pause tour':'Play tour';toggle.setAttribute('aria-label',toggle.textContent);
  if(pending)return;
  let i=0;for(let j=1;j<buttons.length;j++)if(video.currentTime>=times.get(buttons[j].dataset.chapter))i=j;
  const b=buttons[i];if(selected!==b)mark(b);
  const start=i===0?0:times.get(b.dataset.chapter),end=i+1<buttons.length?times.get(buttons[i+1].dataset.chapter):video.duration;
  b.style.setProperty('--progress',String(Math.max(0,Math.min(1,(video.currentTime-start)/(end-start)||0))));
 }
 async function choose(button){
   const current=++request,target=times.get(button.dataset.chapter);pending=true;wantsPlay=true;
   mark(button);showStatus('Loading this view…');sync();
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
    if(wantsPlay)await video.play();if(current===request)showStatus('');
   }catch(error){if(current===request)showStatus(error.message==='Video unavailable'?'The recording could not load. Reload the page to try again.':'Use the video’s play control to continue, then choose a view again.');}
   finally{if(current===request){pending=false;sync();}}
 }
 for(const [index,button] of buttons.entries()){
  button.setAttribute('aria-controls','seven-video');button.setAttribute('aria-pressed','false');
  button.addEventListener('click',()=>choose(button));
  button.addEventListener('keydown',event=>{
   let next;if(event.key==='ArrowRight')next=(index+1)%buttons.length;else if(event.key==='ArrowLeft')next=(index-1+buttons.length)%buttons.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=buttons.length-1;else return;
   event.preventDefault();buttons[next].focus();choose(buttons[next]);
  });
 }
 mark(buttons[0]);
 for(const name of ['timeupdate','play','pause','durationchange','seeked'])video.addEventListener(name,sync);
 toggle.addEventListener('click',async()=>{wantsPlay=pending?!wantsPlay:video.paused;if(pending){if(!wantsPlay)video.pause();sync();return;}if(wantsPlay){try{await video.play();showStatus('');}catch{showStatus('The recording could not load. Reload the page to try again.');}}else video.pause();sync();});
 // The uninterrupted capture is the playlist: chapter selection only seeks.
 // Native pause stays paused, including after scrolling away and returning.
 let resumeOnVisible=false,inView=false,suppressPause=false;
 function pauseOutside(){if(!video.paused){resumeOnVisible=true;suppressPause=true;video.pause();}}
 video.addEventListener('pause',()=>{if(suppressPause)suppressPause=false;else if(!pending){wantsPlay=false;resumeOnVisible=false;}});
 video.addEventListener('play',()=>{wantsPlay=true;});
 const observer=new IntersectionObserver(entries=>{const visible=entries[0].isIntersecting;
  inView=visible;
  if(!visible)pauseOutside();
  else if(!document.hidden&&((wantsPlay&&request===0)||resumeOnVisible)){resumeOnVisible=false;video.play().catch(()=>{});}
 },{threshold:.15});observer.observe(video);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseOutside();else if(resumeOnVisible&&inView){resumeOnVisible=false;video.play().catch(()=>{});}});
 reduced.addEventListener('change',()=>{if(reduced.matches){wantsPlay=false;resumeOnVisible=false;video.pause();}});
 sync();
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
