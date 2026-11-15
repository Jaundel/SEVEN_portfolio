async page=>{
 const pattern='**/seven-full-window.mp4';
 const base='http://127.0.0.1:8765/';
 await page.route(pattern,async route=>{await new Promise(r=>setTimeout(r,2000));await route.continue();});
 try{
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.locator('[data-chapter="cloud-answer"][aria-pressed]').waitFor();
  const before=await page.locator('video').evaluate(v=>v.readyState);
  if(before!==0)throw Error('Rapid test did not reach pre-metadata state');
  for(const name of ['local-answer','live-weather','cloud-answer'])await page.locator(`[data-chapter="${name}"]`).click();
  await page.waitForFunction(()=>{const v=document.querySelector('video');return !v.paused&&!v.seeking&&v.currentTime>=53.7&&v.currentTime<55;},null,{timeout:10000});
  const rapid=await page.locator('video').evaluate(v=>{v.pause();return {time:v.currentTime,error:v.error};});
  const selected=await page.locator('[data-chapter][aria-pressed="true"]').getAttribute('data-chapter');
  if(selected!=='cloud-answer'||rapid.error)throw Error('Older request overrode final selection');
  await page.unroute(pattern);
  await page.route(pattern,route=>route.fulfill({status:404,contentType:'text/plain',body:'Recording unavailable in this controlled test'}));
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.locator('[data-chapter="cloud-answer"][aria-pressed]').waitFor();
  await page.locator('[data-chapter="cloud-answer"]').click();
  try{await page.locator('#video-status').filter({hasText:'Reload the page'}).waitFor({timeout:7000});}
  catch{throw Error(await page.evaluate(()=>{const v=document.querySelector('video');return JSON.stringify({status:document.querySelector('#video-status').textContent,error:v.error?{code:v.error.code,message:v.error.message}:null,network:v.networkState,ready:v.readyState});}));}
  const failure=await page.locator('#video-status').textContent();
  return {passed:true,rapidSelection:{beforeReady:before,selected,...rapid},unavailableMedia:failure};
 }finally{await page.unroute(pattern);await page.goto(base,{waitUntil:'networkidle'});}
}
