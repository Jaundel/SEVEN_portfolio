async page=>{
 const assert=(condition,message)=>{if(!condition)throw Error(message);};
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 const base='http://127.0.0.1:8765/';
 await page.route('**/*',route=>route.continue());
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(base,{waitUntil:'networkidle'});
 const figureWindow=page.waitForEvent('popup');
 await page.locator('.system-figure>a').click();
 const enlarged=await figureWindow;await enlarged.waitForLoadState('domcontentloaded');
 assert(new URL(enlarged.url()).pathname.endsWith('/assets/figures/system-architecture.svg'),'Figure does not open at full size');
 assert(await enlarged.locator('svg').count()===1,'Vector figure not rendered');
 await enlarged.close();
 const manifest=await (await page.request.get(base+'evidence/demo/manifest.json')).json();
 const chapters=[];
 for(const name of manifest.checkpoints.map(c=>c.label)){
  const target=manifest.checkpoints.find(c=>c.label===name).seconds;
  const button=page.locator(`[data-chapter="${name}"]`);
  await button.focus();await button.press('Enter');
  await page.waitForFunction(t=>{const v=document.querySelector('video');return !v.paused&&!v.seeking&&v.currentTime>=t&&v.currentTime<t+1;},target,{timeout:8000});
  const time=await page.locator('video').evaluate(v=>{v.pause();return v.currentTime;});
  chapters.push({name,target,time,keyboard:true});
 }
 const layouts=[];
 await page.locator('#tour-toggle').evaluate(b=>{if(b.textContent==='Pause tour')b.click();});
 await page.evaluate(()=>{for(const i of document.images)i.loading='eager';});
 for(const width of [360,390,768,1440]){
  await page.setViewportSize({width,height:1000});
  await page.waitForFunction(()=>[...document.querySelectorAll('.scientific img')].every(i=>i.complete&&i.naturalWidth>0&&i.currentSrc.includes('-mobile')===matchMedia(i.closest('picture').querySelector('source').media).matches));
  await page.evaluate(async()=>{await document.fonts.ready;for(const i of document.images){i.loading='eager';await i.decode();}scrollTo(0,0);});
  const result=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,fontPoppins:document.fonts.check('14px Poppins'),fontCharter:document.fonts.check('18px Charter'),pictures:[...document.querySelectorAll('.scientific img')].map(i=>({url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,width:i.clientWidth,height:i.clientHeight})),captions:[...document.querySelectorAll('figcaption')].map(c=>({words:c.textContent.trim().split(/\s+/).length,links:c.querySelectorAll('a').length})),smallTableFont:getComputedStyle(document.querySelector('#quality-table')).fontSize,rejectedControls:document.querySelectorAll('#answer-select,#route-select,#capture-controls,.contents').length,tableCellOverflow:[...document.querySelectorAll('th,td')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.textContent)}));
  assert(result.width===result.scroll,'Page overflow at '+width);assert(result.fontPoppins&&result.fontCharter,'Font loading');
  assert(result.pictures.length===5&&result.pictures.every(p=>p.loaded),'Figure loading');
  assert(result.pictures.every(p=>p.url.includes('-mobile')===(p.url.includes('system-architecture')?width<=900:width<=600)),'Wrong figure composition');
  assert(result.captions.length===6&&result.captions.every(c=>c.links===0&&c.words<=35),'Caption clutter');
  assert(result.rejectedControls===0,'Rejected widgets remain');assert(result.tableCellOverflow.length===0,JSON.stringify(result.tableCellOverflow));
  if(width<=600)assert(parseFloat(result.smallTableFont)>=11,'Table too small');
  if([390,1440].includes(width)){
   await page.screenshot({path:`output/playwright/seven-finished-${width}.png`,fullPage:true});
   await page.screenshot({path:`output/playwright/seven-finished-top-${width}.png`});
   await page.locator('#demo').screenshot({path:`output/playwright/seven-finished-demo-${width}.png`});
   for(const id of ['system','routing','answers','energy','measurement'])await page.locator('#'+id).screenshot({path:`output/playwright/seven-finished-${id}-${width}.png`});
  }
  layouts.push(result);
 }
 const links=await page.locator('a[href]').evaluateAll(elements=>[...new Set(elements.map(e=>e.href).filter(h=>h.startsWith(location.origin)&&!h.includes('#')))]);
 await page.goto(base+'supplement.html',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>document.querySelector('#answer-select').options.length===60);
 const records=await (await page.request.get(base+'data/answers.json')).json();
 for(const [index,record]of records.entries()){
  await page.locator('#answer-select').selectOption(String(index));
  assert(await page.locator('#answer-question').textContent()===record.question,'Question '+index);
  assert(await page.locator('#answer-reference').textContent()===record.reference,'Reference '+index);
  const responses=await page.locator('.answer blockquote').allTextContents();
  assert(JSON.stringify(responses)===JSON.stringify(record.answers.map(a=>a.response)),'Response changed '+index);
 }
 await page.locator('#answer-next').click();assert(await page.locator('#answer-select').inputValue()==='0','Next wrap');
 await page.locator('#answer-prev').click();assert(await page.locator('#answer-select').inputValue()==='59','Previous wrap');
 await page.locator('#answer-select').selectOption('0');
 const supplementLayouts=[];
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:1000});
  await page.locator('#power').screenshot({path:`output/playwright/seven-supplement-power-${width}.png`});
  await page.locator('#responses').screenshot({path:`output/playwright/seven-supplement-${width}.png`});
  const l=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert(l.width===l.scroll,'Supplement overflow');supplementLayouts.push(l);
 }
 const extra=await page.locator('a[href]').evaluateAll(elements=>elements.map(e=>e.href).filter(h=>h.startsWith(location.origin)&&!h.includes('#')));
 let checkedLinks=0;
 for(const url of [...new Set([...links,...extra])]){const r=await page.request.head(url);assert(r.ok(),'Bad link '+url);checkedLinks++;}
 assert(errors.length===0,JSON.stringify(errors));
 await page.setViewportSize({width:1440,height:1000});await page.goto(base,{waitUntil:'networkidle'});
 return {passed:true,scope:'Local article and supplement: rendered layouts, figure enlargement, figure loading, caption limits, exact complete responses, eight keyboard gallery selections and local HTTP links.',figureEnlargement:true,layouts,chapters,supplementLayouts,questions:records.length,responses:records.length*3,checkedLinks,errors};
}
