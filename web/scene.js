/* Exports use the same path commands as the canvas renderer. */
window.CaliPlusScene=(function(){
  "use strict";
  const n=value=>Number(value.toFixed(5));

  class SvgPaths {
    constructor(){this.elements=[]}
    beginPath(){this.path=[]}
    moveTo(x,y){this.path.push(`M${n(x)} ${n(y)}`)}
    lineTo(x,y){this.path.push(`L${n(x)} ${n(y)}`)}
    quadraticCurveTo(x,y,ex,ey){this.path.push(`Q${n(x)} ${n(y)} ${n(ex)} ${n(ey)}`)}
    closePath(){this.path.push("Z")}
    rect(x,y,w,h){
      this.moveTo(x,y);this.lineTo(x+w,y);this.lineTo(x+w,y+h);this.lineTo(x,y+h);this.closePath();
    }
    arc(x,y,r){this.ellipse(x,y,r,r)}
    ellipse(x,y,rx,ry){
      if(rx===0||ry===0){this.moveTo(x-rx,y-ry);this.lineTo(x+rx,y+ry);return}
      this.moveTo(x+rx,y);
      this.path.push(`A${n(rx)} ${n(ry)} 0 1 0 ${n(x-rx)} ${n(y)}`,
                     `A${n(rx)} ${n(ry)} 0 1 0 ${n(x+rx)} ${n(y)} Z`);
    }
    stroke(){
      this.elements.push(`<path d="${this.path.join(" ")}" stroke="${this.strokeStyle}" stroke-width="${this.lineWidth}" opacity="${this.globalAlpha}"/>`);
    }
    fill(){this.elements.push(`<path d="${this.path.join(" ")}" fill="${this.fillStyle}" opacity="${this.globalAlpha}"/>`)}
  }

  function exportBounds(D,list){
    const pad=24;
    const [x0,y0,x1,y1]=list.length?D.bounds(list):[0,0,0,0];
    return {x:x0-pad,y:y0-pad,w:x1-x0+2*pad,h:y1-y0+2*pad};
  }

  function exportSvg(D,list,settings){
    const {x,y,w,h}=exportBounds(D,list);
    const scale=Math.min(settings.scale,16384/Math.max(w,h));
    const width=Math.max(1,Math.round(w*scale)),height=Math.max(1,Math.round(h*scale));
    const ctx=new SvgPaths();
    for(const stroke of list)D.drawEl(ctx,stroke,settings.exportDark);
    const keys=["t","c","w","p","pen","hl","closed","ps"];
    const strokes=list.map(stroke=>{
      const model={};
      for(const key of keys)if(key in stroke)model[key]=stroke[key];
      return model;
    });
    const scene=JSON.stringify({version:1,strokes}).replace(/[<>&]/g,c=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[c]));
    const bg=settings.exportBackground?`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${settings.exportDark?"#121212":"#fff"}"/>`:"";
    return {width,svg:`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="${x} ${y} ${w} ${h}"><metadata id="cali-draw-plus">${scene}</metadata>${bg}<g fill="none" stroke-linecap="round" stroke-linejoin="round">${ctx.elements.join("")}</g></svg>`};
  }

  function copyPayload(D,list,settings){
    const {x,y,w,h}=exportBounds(D,list);
    const scale=Math.min(settings.scale,4096/Math.max(w,h));
    const canvas=document.createElement("canvas");
    canvas.width=Math.max(1,Math.ceil(w*scale));canvas.height=Math.max(1,Math.ceil(h*scale));
    const ctx=canvas.getContext("2d");
    if(settings.exportBackground){
      ctx.fillStyle=settings.exportDark?"#121212":"#fff";
      ctx.fillRect(0,0,canvas.width,canvas.height);
    }
    ctx.setTransform(scale,0,0,scale,-x*scale,-y*scale);
    for(const stroke of list)D.drawEl(ctx,stroke,settings.exportDark);
    const png=canvas.toDataURL("image/png").split(",")[1]||"";
    return JSON.stringify({svg:exportSvg(D,list,settings).svg,png});
  }
  return {exportSvg,copyPayload};
})();
