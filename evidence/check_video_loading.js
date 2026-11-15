async page=>{
 const events=[],requests=[];const pattern='**/seven-full-window.mp4';
 await page.setViewportSize({width:1440,height:1000});
 await page.route(pattern,async route=>{requests.push(route.request().headers().range||'full');await new Promise(r=>setTimeout(r,2000));await route.continue();});
 try{
  await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded'});
  await page.evaluate(()=>{const v=document.querySelector('video');window.videoEvents=[];for(const name of ['loadedmetadata','loadeddata','canplay','seeking','seeked','play','playing','error','stalled','suspend'])v.addEventListener(name,()=>window.videoEvents.push({name,time:v.currentTime,ready:v.readyState}));});
  await page.locator('[data-chapter="cloud-answer"][aria-pressed]').waitFor();
  const before=await page.locator('video').evaluate(v=>({ready:v.readyState,time:v.currentTime,network:v.networkState}));
  if(before.ready!==0)throw Error('Test did not reach pre-metadata state');
  await page.locator('[data-chapter="cloud-answer"]').click();
  let passed=true;
  try{await page.waitForFunction(()=>{const v=document.querySelector('video');return !v.paused&&!v.seeking&&v.currentTime>=53.7&&v.currentTime<58;},null,{timeout:12000});}catch{passed=false;}
  const after=await page.evaluate(()=>{const v=document.querySelector('video');v.pause();return {time:v.currentTime,ready:v.readyState,network:v.networkState,error:v.error?{code:v.error.code,message:v.error.message}:null,status:document.querySelector('#video-status').textContent,events:window.videoEvents};});
  if(!passed)throw Error(JSON.stringify({before,after,requests}));
  await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded'});
  await page.locator('[data-chapter="cloud-answer"][aria-pressed]').waitFor();
  await page.locator('[data-chapter="cloud-answer"]').click();
  await page.locator('#tour-toggle').filter({hasText:'Pause tour'}).click();
  await page.waitForFunction(()=>{const v=document.querySelector('video');return v.paused&&!v.seeking&&v.currentTime>=53.7&&v.currentTime<53.8&&document.querySelector('#video-status').hidden;},null,{timeout:12000});
  return {passed,scope:'Cloud selected before metadata, with each genuine MP4 range response delayed by two seconds. Pausing during loading also holds after the selected view becomes ready.',before,after,requests,pendingPauseHolds:true};
 }finally{await page.unroute(pattern);}
}
