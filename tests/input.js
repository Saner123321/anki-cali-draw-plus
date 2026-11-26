// Synthetic pointer sequences executed in the actual Anki blackboard WebEngine.
(() => {
  const canvas=document.getElementById('top');
  const event=(name,id,type,x,y,pressure=.5)=>canvas.dispatchEvent(new PointerEvent(name,{
    bubbles:true,pointerId:id,pointerType:type,clientX:x,clientY:y,pressure,
    isPrimary:id!==3,button:0,buttons:name==='pointerup'?0:1
  }));
  const key=k=>window.dispatchEvent(new KeyboardEvent('keydown',{key:k}));
  const strokes=()=>JSON.parse(ankiBridge.dump()||'[]');
  function check(ok,message){if(!ok)throw new Error(message)}
  try{
    const e=event;
    e('pointerdown',1,'pen',160,160,.15);
    e('pointerdown',2,'touch',180,180);
    e('pointermove',2,'touch',250,220);
    e('pointerup',2,'touch',250,220);
    e('pointermove',1,'pen',200,160,.8);
    e('pointermove',1,'pen',280,160,.65);
    e('pointerup',1,'pen',280,160,0);
    const first=strokes()[0];
    check(first.pen&&first.p.length===3&&Math.abs(first.p[1][3]-.8)<.01,'pen ownership or pressure lost');
    check(first.p[1][2]<first.p[1][3],'pressure smoothing lost');
    e('pointerdown',4,'mouse',175,245);
    e('pointermove',4,'mouse',250,245);
    e('lostpointercapture',4,'mouse',250,245);
    check(strokes().length===2&&!strokes()[1].pen,'mouse lost capture');
    key('e');e('pointerdown',4,'mouse',187,245);e('pointerup',4,'mouse',187,245);
    check(strokes().length===1,'eraser failed');
    window.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true}));
    check(strokes().length===2,'undo failed');
    window.dispatchEvent(new KeyboardEvent('keydown',{key:'y',ctrlKey:true}));
    check(strokes().length===1,'redo failed');
    window.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true}));
    key('r');e('pointerdown',4,'mouse',165,260);e('pointermove',4,'mouse',245,295);e('pointerup',4,'mouse',245,295);
    check(strokes()[2].t==='rect','shape failed');
    key('v');e('pointerdown',4,'mouse',205,276);e('pointermove',4,'mouse',250,280);e('pointerup',4,'mouse',250,280);
    check(strokes()[2].p[0][0]===210,'selection move failed');
    e('pointerdown',4,'mouse',293,302);e('pointermove',4,'mouse',315,318);e('pointerup',4,'mouse',315,318);
    check(strokes()[2].p[1][0]>290,'selection scale failed');
    const shape=strokes()[2],cx=(shape.p[0][0]+shape.p[1][0])/2,top=shape.p[0][1]-shape.w;
    e('pointerdown',4,'mouse',cx,top-28);e('pointermove',4,'mouse',cx+60,top+20);e('pointerup',4,'mouse',cx+60,top+20);
    check(strokes()[2].t==='poly','selection rotation failed');
    key('p');ankiBridge.configure({cursorShape:'hidden'});
    check(canvas.style.cursor==='none','hidden cursor failed');
    ankiBridge.configure({cursorShape:'ring',cursorSize:14});
    check(canvas.style.cursor.includes('14')&&canvas.style.cursor.includes('circle'),'ring cursor failed');
    ankiBridge.configure({cursorShape:'dot',cursorSize:8});
    check(canvas.style.cursor.includes('8')&&canvas.style.cursor.includes('circle'),'dot cursor failed');
    return 'ok';
  }catch(error){return error.message}
})()
