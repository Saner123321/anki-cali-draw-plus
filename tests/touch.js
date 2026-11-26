// Run after the pen release grace period. Coordinates verify the world transform.
(() => {
  const canvas=document.getElementById('top');
  const e=(name,id,type,x,y)=>canvas.dispatchEvent(new PointerEvent(name,{
    bubbles:true,pointerId:id,pointerType:type,clientX:x,clientY:y,
    isPrimary:id!==3,button:0,buttons:name==='pointerup'?0:1
  }));
  const t=(name,id,x,y)=>e('pointer'+name,id,'touch',x,y);
  const strokes=()=>JSON.parse(ankiBridge.dump());
  t('down',2,130,120);t('move',2,170,150);t('up',2,170,150);
  e('pointerdown',4,'mouse',220,200);e('pointerup',4,'mouse',220,200);
  const one=strokes()[3].p[0];
  if(one[0]!==180||one[1]!==170)return 'single-finger pan failed';
  t('down',2,100,130);t('down',3,200,130);
  t('move',2,110,155);t('move',3,210,155);
  t('move',2,60,155);t('move',3,260,155);
  t('up',2,60,155);t('up',3,260,155);
  e('pointerdown',4,'mouse',160,155);e('pointerup',4,'mouse',160,155);
  const two=strokes()[4].p[0];
  if(Math.abs(two[0]-110)>.01||Math.abs(two[1]-100)>.01)return 'two-finger midpoint or scale failed';
  if(strokes()[4].w!==1.5)return 'pinch did not double zoom';
  window.dispatchEvent(new KeyboardEvent('keydown',{key:'h'}));
  [...document.querySelectorAll('button')].find(b=>b.textContent==='Insert into note').click();
  return 'ok';
})()
