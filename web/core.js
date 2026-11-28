/* Anki-Cali Draw core: the drawing engine and UI helpers shared by the blackboard page and the
   on-card annotation overlay. Written for old Chromium (no ?. / ?? / CSS inset). */
window.CaliPlusCore=window.CaliPlusCore||(function(){
"use strict";

/* ------------------------------------------------------------------ icons / css / dom helpers */
const P={
 select:'<path d="M5 3l14 8-6 2-2 6z"/>',
 pen:'<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
 hl:'<path d="M9 11l-6 6v3h9l3-3"/><path d="M22 12l-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>',
 line:'<path d="M5 19L19 5"/>',arrow:'<path d="M5 19L19 5M9 5h10v10"/>',
 rect:'<rect x="4" y="5" width="16" height="14" rx="2"/>',ellipse:'<ellipse cx="12" cy="12" rx="9" ry="7"/>',
 eraser:'<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/>',
 hand:'<path d="M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20"/>',
 move:'<path d="M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20"/>',
 pointer:'<path d="M5 3l14 8-6 2-2 6z"/>',
 undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
 redo:'<path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
 trash:'<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/>',
 copy:'<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
 paste:'<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M8 4H5v17h14V4h-3M8 11h8m-8 5h5"/>',
 image:'<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="1"/><path d="m3 17 5-4 3 2 4-5 6 6"/>',
 save:'<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
 minus:'<path d="M5 12h14"/>',plus:'<path d="M12 5v14M5 12h14"/>',
 fit:'<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
 gear:'<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/>',
 eye:'<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 close:'<path d="M6 6l12 12M18 6L6 18"/>'
};
const svg=(p,w)=>'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="'+(w||2)+'" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>';
const el=(tag,cls,html)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e};
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));

function localizer(settings){
  const tr=(source,values)=>{
    const message=(settings.strings&&settings.strings[source])||source;
    return values?message.replace(/\{(\w+)\}/g,(_,key)=>values[key]):message;
  };
  function tip(node,source){
    node.setAttribute("data-cali-tip",source);
    node.setAttribute("data-tip",tr(source));
    node.setAttribute("aria-label",tr(source));
  }
  function refresh(root){
    for(const node of root.querySelectorAll("[data-cali-tip]"))tip(node,node.getAttribute("data-cali-tip"));
  }
  return {tr,tip,refresh};
}

const CSS=`
.ad-root{--fg:#1e1e1e;--isl:#fff;--bd:#e1e1ea;--ac:#6965db;--acl:#e3e2fe;--on:#fff;--mut:#7a7a8c;color:var(--fg);font:13px system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-user-select:none;user-select:none}
.ad-root.dark{--fg:#e6e6e6;--isl:#2a2a31;--bd:#454552;--ac:#a8a5ff;--acl:#3e3c66;--on:#121212;--mut:#9a9aab}
.ad-root *{box-sizing:border-box}
.ad-ui{transition:opacity .15s}
.ad-isl{display:flex;gap:2px;align-items:center;background:var(--isl);border:1px solid var(--bd);border-radius:12px;padding:4px;box-shadow:0 2px 12px rgba(0,0,0,.18);cursor:default}
.ad-root button{display:inline-flex;align-items:center;justify-content:center;gap:6px;background:none;border:0;color:var(--fg);border-radius:8px;min-width:32px;height:32px;padding:0 7px;cursor:pointer;font:inherit}
.ad-root button:hover{background:rgba(127,127,127,.2)}
.ad-root button.on{background:var(--acl);color:var(--ac)}
.ad-root button.pri{background:var(--ac);color:var(--on);font-weight:600;padding:0 12px}
.ad-root button.txt{padding:0 12px}
.ad-root .ad-sw{min-width:22px;width:22px;height:22px;padding:0;border-radius:50%;border:2px solid var(--isl);box-shadow:0 0 0 1px var(--bd)}
.ad-root .ad-sw.on{box-shadow:0 0 0 2px var(--ac)}
.ad-root .ad-spec{background:conic-gradient(#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00)}
.ad-sep{background:var(--bd);width:1px;height:20px;margin:0 4px;flex:none}
.ad-vert .ad-sep{width:20px;height:1px;margin:3px 0}
.ad-root svg{display:block}
.ad-wrap{display:flex;align-items:center;gap:6px;padding:0 4px}
.ad-slider{position:relative;background:var(--bd);border-radius:4px;cursor:pointer;touch-action:none;flex:none}
.ad-slider::after{content:"";position:absolute;left:-9px;right:-9px;top:-7px;bottom:-7px}
.ad-slider.v{width:6px;height:84px}
.ad-slider.h{height:6px;width:84px}
.ad-sfill{position:absolute;left:0;bottom:0;background:var(--ac);border-radius:4px;pointer-events:none}
.ad-slider.v .ad-sfill{width:100%}.ad-slider.h .ad-sfill{height:100%}
.ad-sthumb{position:absolute;width:14px;height:14px;border-radius:50%;background:var(--isl);border:2px solid var(--ac);pointer-events:none;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.ad-slider.v .ad-sthumb{left:-4px}.ad-slider.h .ad-sthumb{top:-4px}
.ad-wl{min-width:26px;text-align:center;color:var(--mut);font-variant-numeric:tabular-nums}
.ad-wdot{display:flex;align-items:center;justify-content:center;width:22px;height:22px}
.ad-wdot i{display:block;border-radius:50%;background:var(--fg);max-width:20px;max-height:20px;min-width:2px;min-height:2px}
.ad-vert .ad-wrap{flex-direction:column;padding:2px 0;gap:8px}
.ad-tip{position:fixed;left:0;top:0;z-index:2147483647;background:var(--fg);color:var(--isl);padding:5px 9px;border-radius:7px;font-size:12px;pointer-events:none;opacity:0;transition:opacity .12s;white-space:nowrap}
.ad-tip.show{opacity:1}
.ad-ring{position:fixed;left:0;top:0;border:2px solid var(--fg);background:rgba(127,127,127,.18);border-radius:50%;pointer-events:none;display:none;z-index:6}
.ad-pop{position:fixed;z-index:8;width:204px;padding:10px;background:var(--isl);border:1px solid var(--bd);border-radius:12px;box-shadow:0 6px 22px rgba(0,0,0,.3);cursor:default}
.ad-pop canvas{display:block;width:180px;height:120px;border-radius:6px;cursor:crosshair;touch-action:none}
.ad-pop input[type=range]{display:block;width:180px;margin:8px 0;height:12px;border-radius:6px;-webkit-appearance:none;appearance:none;background:linear-gradient(90deg,#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00)}
.ad-pop input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid #444}
.ad-row{display:flex;align-items:center;gap:8px}
.ad-prev{width:26px;height:26px;border-radius:6px;border:1px solid var(--bd);flex:none}
.ad-hex{flex:1;min-width:0;border:1px solid var(--bd);background:transparent;color:var(--fg);border-radius:6px;padding:4px 6px;font:12px ui-monospace,Consolas,monospace;-webkit-user-select:text;user-select:text}
.ad-fl{margin:8px 0 6px;color:var(--mut);font-size:11px;line-height:1.3}
.ad-favs{display:flex;gap:6px}
.ad-root.zen .ad-ui,.ad-root.writing .ad-ui,.ad-root.zen .ad-pop,.ad-root.writing .ad-pop{opacity:0!important;pointer-events:none!important}
/* while zen mode hides the tools, one faint eye stays so you can always bring them back (also on touch screens) */
.ad-root .ad-ghost{display:none;position:fixed;top:10px;right:10px;z-index:7;width:32px;height:32px;min-width:32px;padding:0;border-radius:50%;
  color:#e03131;background:var(--isl);border:1px solid #e03131;box-shadow:0 1px 6px rgba(0,0,0,.2);opacity:.4;transition:opacity .15s;pointer-events:auto}
.ad-root.zen .ad-ghost{display:inline-flex}
.ad-root .ad-ghost:hover{opacity:1;background:var(--isl);color:#e03131}
.ad-root.shot .ad-ui,.ad-root.shot .ad-ring,.ad-root.shot .ad-pop,.ad-root.shot .ad-ghost{visibility:hidden}
`;

function hsv2hex(h,s,v){
  const f=n=>{const k=(n+h/60)%6;return v-v*s*Math.max(0,Math.min(k,4-k,1))};
  const x=n=>("0"+Math.round(f(n)*255).toString(16)).slice(-2);return"#"+x(5)+x(3)+x(1)}
function hex2hsv(hex){
  const m=/^#?([0-9a-f]{6})$/i.exec(hex||"");if(!m)return null;
  const n=parseInt(m[1],16),r=(n>>16&255)/255,g=(n>>8&255)/255,b=(n&255)/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn;
  let h=0;if(d){h=mx===r?((g-b)/d)%6:mx===g?(b-r)/d+2:(r-g)/d+4;h=(h*60+360)%360}
  return[h,mx?d/mx:0,mx]}

/* ------------------------------------------------------------------ tooltips (HTML, not native)
   Native title="" tooltips are OS windows: on a see-through window they render as black bars. */
function installTips(root){
  const tip=el("div","ad-tip");root.appendChild(tip);let t=null;
  const hide=()=>{clearTimeout(t);tip.classList.remove("show")};
  root.addEventListener("pointerover",e=>{
    const b=e.target.closest?e.target.closest("[data-tip]"):null;if(!b)return;
    clearTimeout(t);
    t=setTimeout(()=>{tip.textContent=b.getAttribute("data-tip");tip.classList.add("show");
      const r=b.getBoundingClientRect(),tw=tip.offsetWidth,th=tip.offsetHeight;
      let x=r.left+r.width/2-tw/2,y=r.bottom+8;if(y+th>innerHeight-4)y=r.top-th-8;
      x=clamp(x,4,innerWidth-tw-4);tip.style.transform="translate("+x+"px,"+y+"px)"},350)});
  root.addEventListener("pointerout",e=>{if(e.target.closest&&e.target.closest("[data-tip]"))hide()});
  root.addEventListener("pointerdown",hide,true);
}

/* ------------------------------------------------------------------ custom slider (vertical or horizontal)
   Native vertical <input type=range> is inconsistent between Chromium versions, so draw our own. */
function makeSlider(o){
  const box=el("div","ad-slider "+(o.vertical?"v":"h")),fill=el("i","ad-sfill"),thumb=el("b","ad-sthumb");
  box.appendChild(fill);box.appendChild(thumb);if(o.tip)box.setAttribute("data-tip",o.tip);
  let v=o.value,activePointer=null;
  function paint(){const f=clamp((v-o.min)/(o.max-o.min),0,1)*100;
    if(o.vertical){fill.style.height=f+"%";thumb.style.bottom="calc("+f+"% - 7px)"}
    else{fill.style.width=f+"%";thumb.style.left="calc("+f+"% - 7px)"}}
  function fromEvent(e){
    const r=box.getBoundingClientRect(),f=clamp(o.vertical?1-(e.clientY-r.top)/r.height:(e.clientX-r.left)/r.width,0,1);
    const nv=clamp(Math.round((o.min+f*(o.max-o.min))/o.step)*o.step,o.min,o.max);
    if(nv!==v){v=nv;paint();o.onInput(v)}}
  box.addEventListener("pointerdown",e=>{
    if(activePointer!==null||e.button!==0)return;
    activePointer=e.pointerId;try{box.setPointerCapture(e.pointerId)}catch(_){}fromEvent(e);
  });
  box.addEventListener("pointermove",e=>{if(e.pointerId===activePointer)fromEvent(e)});
  ["pointerup","pointercancel","lostpointercapture"].forEach(n=>box.addEventListener(n,e=>{
    if(e.pointerId===activePointer){activePointer=null;if(o.onChange)o.onChange(v)}
  }));
  paint();
  return{el:box,set(nv){if(activePointer===null&&v!==nv){v=nv;paint();o.onInput(v)}}};
}

function makeWidthControl(D,L,vertical,persist){
  const wrap=el("div","ad-wrap"),dot=el("div","ad-wdot","<i></i>"),label=el("div","ad-wl");
  function setWidth(width){
    D.setWidth(width);
    label.textContent=width;
    dot.firstChild.style.width=dot.firstChild.style.height=Math.min(20,Math.max(2,width))+"px";
  }
  const slider=makeSlider({min:1,max:40,step:.5,value:D.width,vertical,onInput:setWidth,
    onChange:width=>{D.applyWidthToSelection();persist(width)}});
  L.tip(slider.el,vertical?"Pen thickness (slide up = thicker)":"Pen thickness (slide right = thicker)");
  wrap.appendChild(dot);wrap.appendChild(slider.el);wrap.appendChild(label);
  setWidth(D.width);
  return {el:wrap,restore:slider.set};
}

/* ------------------------------------------------------------------ colour picker + 5 favourites */
function makePicker(h){
  const pop=el("div","ad-pop ad-ui",
    '<canvas class="ad-sv" width="180" height="120"></canvas><input class="ad-hue" type="range" min="0" max="360" step="1">'+
    '<div class="ad-row"><span class="ad-prev"></span><input class="ad-hex" maxlength="7" spellcheck="false"></div>'+
    '<div class="ad-fl"></div><div class="ad-favs"></div>');
  pop.style.display="none";h.parent.appendChild(pop);
  const sv=pop.querySelector(".ad-sv"),hue=pop.querySelector(".ad-hue"),hex=pop.querySelector(".ad-hex"),
        prev=pop.querySelector(".ad-prev"),slots=pop.querySelector(".ad-favs"),g=sv.getContext("2d");
  let H=0,S=1,V=1,dragging=false;
  const cur=()=>hsv2hex(H,S,V);
  function paint(){
    g.clearRect(0,0,180,120);g.fillStyle="hsl("+H+",100%,50%)";g.fillRect(0,0,180,120);
    let a=g.createLinearGradient(0,0,180,0);a.addColorStop(0,"#fff");a.addColorStop(1,"rgba(255,255,255,0)");g.fillStyle=a;g.fillRect(0,0,180,120);
    a=g.createLinearGradient(0,0,0,120);a.addColorStop(0,"rgba(0,0,0,0)");a.addColorStop(1,"#000");g.fillStyle=a;g.fillRect(0,0,180,120);
    g.lineWidth=2;g.strokeStyle="#fff";g.beginPath();g.arc(S*180,(1-V)*120,6,0,7);g.stroke();
    g.lineWidth=1;g.strokeStyle="#000";g.beginPath();g.arc(S*180,(1-V)*120,7.5,0,7);g.stroke();
  }
  function changed(final){const c=cur();prev.style.background=c;hex.value=c;paint();h.onPick(c,!!final)}
  function setHex(c){const a=hex2hsv(c);if(!a)return false;H=a[0];S=a[1];V=a[2];hue.value=H;prev.style.background=c;hex.value=c;paint();return true}
  const at=e=>{const r=sv.getBoundingClientRect();S=clamp((e.clientX-r.left)/r.width,0,1);V=1-clamp((e.clientY-r.top)/r.height,0,1);changed(false)};
  sv.addEventListener("pointerdown",e=>{dragging=true;try{sv.setPointerCapture(e.pointerId)}catch(_){}at(e)});
  sv.addEventListener("pointermove",e=>{if(dragging)at(e)});
  ["pointerup","pointercancel"].forEach(n=>sv.addEventListener(n,()=>{if(dragging){dragging=false;changed(true)}}));
  hue.addEventListener("input",()=>{H=+hue.value;changed(false)});
  hue.addEventListener("change",()=>changed(true));
  hex.addEventListener("change",()=>{let v=hex.value.trim();if(v[0]!=="#")v="#"+v;if(setHex(v))h.onPick(cur(),true);else hex.value=cur()});
  hex.addEventListener("keydown",e=>e.stopPropagation());
  function renderFavs(){
    pop.querySelector(".ad-fl").textContent=h.tr("Favourites: click a slot to save this colour there");
    slots.innerHTML="";
    h.getFavs().forEach((c,i)=>{const b=el("button","ad-sw");b.style.background=c;b.setAttribute("data-tip",h.tr("Save this colour in slot {number}",{number:i+1}));
      b.onclick=()=>{const f=h.getFavs().slice();f[i]=cur();h.setFavs(f);renderFavs()};slots.appendChild(b)});
  }
  const api={
    el:pop,renderFavs,
    isOpen:()=>pop.style.display!=="none",
    open(){const c=h.getColor();setHex(c==="auto"?"#e03131":c);renderFavs();pop.style.display="block";h.place(pop)},
    close(){pop.style.display="none"},
    toggle(){api.isOpen()?api.close():api.open()}
  };
  h.parent.addEventListener("pointerdown",e=>{
    if(!api.isOpen()||pop.contains(e.target))return;
    if(e.target.closest&&e.target.closest("[data-spec]"))return;
    api.close()},true);
  return api;
}

/* ------------------------------------------------------------------ the drawing engine */
function penCursor(shape,size){
  if(shape==="hidden")return "none";
  size=clamp(Math.round(Number(size)||24),6,48);
  const mark=shape==="dot"?"<circle cx='12' cy='12' r='4' fill='#111' stroke='#fff' stroke-width='2'/>":
    shape==="ring"?"<circle cx='12' cy='12' r='8' stroke='#fff' stroke-width='4'/><circle cx='12' cy='12' r='8' stroke='#111' stroke-width='2'/>":
    "<path d='M12 3v6M12 15v6M3 12h6M15 12h6' stroke='#fff' stroke-width='3.4'/><path d='M12 3v6M12 15v6M3 12h6M15 12h6' stroke='#111' stroke-width='1.4'/>";
  const svg="<svg xmlns='http://www.w3.org/2000/svg' width='"+size+"' height='"+size+"' viewBox='0 0 24 24'><g fill='none' stroke-linecap='round'>"+mark+"</g></svg>";
  const center=Math.floor(size/2);
  return 'url("data:image/svg+xml,'+encodeURIComponent(svg)+'") '+center+' '+center+', crosshair';
}
const RESIZE_CURSOR={nw:"nwse-resize",se:"nwse-resize",ne:"nesw-resize",sw:"nesw-resize",n:"ns-resize",s:"ns-resize",e:"ew-resize",w:"ew-resize",rot:"grab"};

function engine(o){
  const base=o.base,top=o.top,view=o.view,docMode=!!o.docMode,S=o.S,hooks=o.hooks||{},ring=o.ring;
  const bctx=base.getContext("2d"),tctx=top.getContext("2d");
  const ZMIN=.25,ZMAX=100,ER=10;
  let els=[],undo=[],redo=[],drag=null,sel=new Set(),selBox=null,nextId=1;
  let tool="pen",color="auto",width=S.penWidth||3,dpr=1,space=false,showSel=true;
  let owner=null, lastPen=-Infinity, touchFrame=0, touchStarted=false;
  let cursor=penCursor(S.cursorShape,S.cursorSize);
  const touches=new Map();
  const newId=()=>nextId++;
  const isDark=()=>o.isDark();
  const accent=()=>o.accent()||"#6965db";
  const inkOf=d=>d?(o.inkDark||"#e6e6e6"):(o.inkLight||"#1e1e1e");
  const sync=()=>{if(docMode){view.x=-scrollX;view.y=-scrollY;view.z=1}};

  /* ---- drawing ---- */
  function applyView(c){c.setTransform(dpr*view.z,0,0,dpr*view.z,dpr*view.x,dpr*view.y)}
  function drawEl(ctx,e,dark){
    const col=e.c==="auto"?(e.hl?"#ffd43b":inkOf(dark)):e.c;
    ctx.strokeStyle=ctx.fillStyle=col;ctx.lineWidth=e.w;ctx.lineCap=ctx.lineJoin="round";ctx.globalAlpha=e.hl?.38:1;ctx.beginPath();
    const p=e.p;
    if(e.t==="pen"){
      if(p.length===1){ctx.arc(p[0][0],p[0][1],e.w/2,0,7);ctx.fill();ctx.globalAlpha=1;return}
      const ps=e.ps===undefined?.6:e.ps;
      if(e.pen&&ps>0){                                  // pressure: width follows the stylus along the stroke
        let prev=p[0];
        for(let i=1;i<p.length;i++){
          const nx=i<p.length-1?[(p[i][0]+p[i+1][0])/2,(p[i][1]+p[i+1][1])/2]:p[i];
          ctx.beginPath();ctx.moveTo(prev[0],prev[1]);ctx.quadraticCurveTo(p[i][0],p[i][1],nx[0],nx[1]);
          const pr=p[i][2]===undefined?.5:p[i][2];
          ctx.lineWidth=Math.max(.15*e.w,e.w*(1+ps*1.6*(pr-.5)));ctx.stroke();prev=nx}
        return}
      ctx.moveTo(p[0][0],p[0][1]);
      for(let i=1;i<p.length-1;i++)ctx.quadraticCurveTo(p[i][0],p[i][1],(p[i][0]+p[i+1][0])/2,(p[i][1]+p[i+1][1])/2);
      ctx.lineTo(p[p.length-1][0],p[p.length-1][1]);
    }else if(e.t==="poly"){
      ctx.moveTo(p[0][0],p[0][1]);for(let i=1;i<p.length;i++)ctx.lineTo(p[i][0],p[i][1]);if(e.closed)ctx.closePath();
    }else{
      const x1=p[0][0],y1=p[0][1],x2=p[1][0],y2=p[1][1];
      if(e.t==="rect")ctx.rect(x1,y1,x2-x1,y2-y1);
      else if(e.t==="ellipse")ctx.ellipse((x1+x2)/2,(y1+y2)/2,Math.abs(x2-x1)/2,Math.abs(y2-y1)/2,0,0,7);
      else{ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);
        if(e.t==="arrow"){const a=Math.atan2(y2-y1,x2-x1),h=10+e.w*2;for(const s of[-.5,.5]){ctx.moveTo(x2,y2);ctx.lineTo(x2-h*Math.cos(a+s),y2-h*Math.sin(a+s))}}}
    }
    ctx.stroke();ctx.globalAlpha=1;
  }
  function redraw(skip){
    sync();bctx.setTransform(1,0,0,1,0,0);bctx.clearRect(0,0,base.width,base.height);applyView(bctx);
    for(const e of els)if(!(skip&&skip.has(e.id)))drawEl(bctx,e,isDark());
    if(hooks.zoom)hooks.zoom(view.z);renderTop();
  }
  function resize(){dpr=devicePixelRatio||1;for(const c of[base,top]){c.width=innerWidth*dpr;c.height=innerHeight*dpr}redraw()}

  /* ---- history ---- */
  const commit=n=>{undo.push(els);redo=[];els=n};
  const pruneSel=()=>{const ids=new Set(els.map(e=>e.id));sel=new Set([...sel].filter(i=>ids.has(i)))};
  function doUndo(){finish();if(undo.length){redo.push(els);els=undo.pop();pruneSel();redraw();updateSel()}}
  function doRedo(){finish();if(redo.length){undo.push(els);els=redo.pop();pruneSel();redraw();updateSel()}}
  function doClear(){finish();if(els.length){commit([]);sel=new Set();redraw();updateSel()}}
  function delSel(){if(sel.size){commit(els.filter(e=>!sel.has(e.id)));sel=new Set();redraw();updateSel()}}

  /* ---- geometry ---- */
  function bounds(list){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
    for(const e of list){const m=e.w+(e.t==="arrow"?10+2*e.w:0);
      for(const q of e.p){x0=Math.min(x0,q[0]-m);y0=Math.min(y0,q[1]-m);x1=Math.max(x1,q[0]+m);y1=Math.max(y1,q[1]+m)}}
    return[x0,y0,x1,y1]}
  function segD(px,py,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,l=dx*dx+dy*dy;let t=l?((px-ax)*dx+(py-ay)*dy)/l:0;t=Math.max(0,Math.min(1,t));return Math.hypot(px-ax-t*dx,py-ay-t*dy)}
  function hit(e,x,y,px){
    const r=Math.max((px||8)/view.z+e.w/2,e.hl?e.w/2:0),p=e.p;
    if(e.t==="pen"||e.t==="poly"){
      if(p.length===1)return Math.hypot(x-p[0][0],y-p[0][1])<r;
      for(let i=1;i<p.length;i++)if(segD(x,y,p[i-1][0],p[i-1][1],p[i][0],p[i][1])<r)return true;
      return !!e.closed&&segD(x,y,p[p.length-1][0],p[p.length-1][1],p[0][0],p[0][1])<r}
    const x1=p[0][0],y1=p[0][1],x2=p[1][0],y2=p[1][1];
    if(e.t==="line"||e.t==="arrow")return segD(x,y,x1,y1,x2,y2)<r;
    if(e.t==="rect")return segD(x,y,x1,y1,x2,y1)<r||segD(x,y,x2,y1,x2,y2)<r||segD(x,y,x2,y2,x1,y2)<r||segD(x,y,x1,y2,x1,y1)<r;
    const rx=Math.abs(x2-x1)/2||1,ry=Math.abs(y2-y1)/2||1;
    return Math.abs(Math.hypot((x-(x1+x2)/2)/rx,(y-(y1+y2)/2)/ry)-1)*Math.min(rx,ry)<r;
  }
  function inPoly(p,x,y){let c=false;for(let i=0,j=p.length-1;i<p.length;j=i++){
    if((p[i][1]>y)!==(p[j][1]>y)&&x<(p[j][0]-p[i][0])*(y-p[i][1])/(p[j][1]-p[i][1])+p[i][0])c=!c}return c}
  function hitSelect(e,x,y){                         // outline (generous) or the inside of a shape
    if(hit(e,x,y,14))return true;
    if(e.t==="rect"){const x1=e.p[0][0],y1=e.p[0][1],x2=e.p[1][0],y2=e.p[1][1];return x>=Math.min(x1,x2)&&x<=Math.max(x1,x2)&&y>=Math.min(y1,y2)&&y<=Math.max(y1,y2)}
    if(e.t==="ellipse"){const x1=e.p[0][0],y1=e.p[0][1],x2=e.p[1][0],y2=e.p[1][1];return Math.hypot((x-(x1+x2)/2)/(Math.abs(x2-x1)/2||1),(y-(y1+y2)/2)/(Math.abs(y2-y1)/2||1))<=1}
    if(e.t==="poly"&&e.closed)return inPoly(e.p,x,y);
    return false}
  function samplePts(e){const p=e.p;if(e.t==="pen"||e.t==="poly")return p;
    const x1=p[0][0],y1=p[0][1],x2=p[1][0],y2=p[1][1],cx=(x1+x2)/2,cy=(y1+y2)/2;
    if(e.t==="rect")return[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[cx,y1],[x2,cy],[cx,y2],[x1,cy]];
    if(e.t==="ellipse"){const a=[];for(let i=0;i<12;i++){const t=i*Math.PI/6;a.push([cx+Math.cos(t)*(x2-x1)/2,cy+Math.sin(t)*(y2-y1)/2])}return a}
    return[[x1,y1],[cx,cy],[x2,y2]]}
  function erase(x,y){const k=els.filter(e=>!hit(e,x,y,ER));if(k.length!==els.length){els=k;redraw()}}

  /* ---- transforms (move / resize / rotate). Everything is baked into the points. ---- */
  function toPoly(e){
    const x1=e.p[0][0],y1=e.p[0][1],x2=e.p[1][0],y2=e.p[1][1];let pts;
    if(e.t==="rect")pts=[[x1,y1],[x2,y1],[x2,y2],[x1,y2]];
    else{pts=[];const cx=(x1+x2)/2,cy=(y1+y2)/2,rx=(x2-x1)/2,ry=(y2-y1)/2;for(let i=0;i<180;i++){const t=i*Math.PI/90;pts.push([cx+Math.cos(t)*rx,cy+Math.sin(t)*ry])}}
    return Object.assign({},e,{t:"poly",closed:true,p:pts})}
  const shift=(e,dx,dy)=>Object.assign({},e,{p:e.p.map(q=>[q[0]+dx,q[1]+dy].concat(q.slice(2)))});
  function xf(e,T){
    if(T.k==="s")return Object.assign({},e,{p:e.p.map(q=>[T.ax+(q[0]-T.ax)*T.sx,T.ay+(q[1]-T.ay)*T.sy].concat(q.slice(2)))});
    const ee=(e.t==="rect"||e.t==="ellipse")?toPoly(e):e,c=Math.cos(T.th),s=Math.sin(T.th);
    return Object.assign({},ee,{p:ee.p.map(q=>{const dx=q[0]-T.cx,dy=q[1]-T.cy;return[T.cx+dx*c-dy*s,T.cy+dx*s+dy*c].concat(q.slice(2))})})}
  const selected=()=>els.filter(e=>sel.has(e.id));
  function handles(){
    if(!selBox)return[];const x0=selBox[0],y0=selBox[1],x1=selBox[2],y1=selBox[3],cx=(x0+x1)/2,cy=(y0+y1)/2;
    return[["nw",x0,y0],["n",cx,y0],["ne",x1,y0],["e",x1,cy],["se",x1,y1],["s",cx,y1],["sw",x0,y1],["w",x0,cy],["rot",cx,y0-28/view.z]]}
  const handleAt=(x,y)=>handles().find(h=>Math.hypot(x-h[1],y-h[2])<=11/view.z);
  function anchorOf(name){const x0=selBox[0],y0=selBox[1],x1=selBox[2],y1=selBox[3],cx=(x0+x1)/2,cy=(y0+y1)/2;
    return{nw:[x1,y1],n:[cx,y1],ne:[x0,y1],e:[x0,cy],se:[x0,y0],s:[cx,y0],sw:[x1,y0],w:[x1,cy]}[name]}

  /* ---- overlay canvas: live stroke, selection box + handles, marquee ---- */
  function renderTop(){
    sync();tctx.setTransform(1,0,0,1,0,0);tctx.clearRect(0,0,top.width,top.height);applyView(tctx);
    const d=drag,z=view.z;let box=selBox,ox=0,oy=0,list=null;
    if(d&&d.k==="draw")drawEl(tctx,d.el,isDark());
    if(d&&d.k==="move"){ox=d.dx;oy=d.dy;tctx.save();tctx.translate(ox,oy);for(const e of selected())drawEl(tctx,e,isDark());tctx.restore()}
    if(d&&d.k==="xform"&&d.T){list=selected().map(e=>xf(e,d.T));for(const e of list)drawEl(tctx,e,isDark());box=bounds(list)}
    if(box&&showSel&&tool==="select"){
      const x0=box[0]+ox,y0=box[1]+oy,w=box[2]-box[0],h=box[3]-box[1];
      tctx.save();tctx.strokeStyle=accent();tctx.lineWidth=1.5/z;tctx.setLineDash([6/z,4/z]);tctx.strokeRect(x0,y0,w,h);tctx.setLineDash([]);
      if(!(d&&d.k==="xform")){
        const hs=8/z;tctx.fillStyle="#fff";tctx.lineWidth=1.5/z;
        for(const h2 of handles()){
          if(h2[0]==="rot"){tctx.beginPath();tctx.moveTo((box[0]+box[2])/2+ox,y0);tctx.lineTo(h2[1]+ox,h2[2]+oy);tctx.stroke();tctx.beginPath();tctx.arc(h2[1]+ox,h2[2]+oy,5.5/z,0,7);tctx.fill();tctx.stroke()}
          else{tctx.fillRect(h2[1]+ox-hs/2,h2[2]+oy-hs/2,hs,hs);tctx.strokeRect(h2[1]+ox-hs/2,h2[2]+oy-hs/2,hs,hs)}}}
      tctx.restore()}
    if(d&&d.k==="marquee"){tctx.save();tctx.strokeStyle=accent();tctx.fillStyle=accent();tctx.lineWidth=1/z;tctx.setLineDash([5/z,3/z]);
      tctx.globalAlpha=.12;tctx.fillRect(d.x0,d.y0,d.x1-d.x0,d.y1-d.y0);tctx.globalAlpha=1;tctx.strokeRect(d.x0,d.y0,d.x1-d.x0,d.y1-d.y0);tctx.restore()}
  }
  function updateSel(){
    selBox=sel.size?bounds(selected()):null;
    if(hooks.sel)hooks.sel(sel.size);renderTop();
  }

  /* ---- cursors: one consistent set everywhere ---- */
  const setCursor=c=>{if(top.style.cursor!==c)top.style.cursor=c};
  function updateCursor(x,y){
    if(tool==="eraser")return setCursor("none");
    if(tool==="hand")return setCursor(drag&&drag.k==="pan"?"grabbing":"grab");
    if(tool==="select"){
      if(drag&&drag.k==="move")return setCursor("move");
      if(drag&&drag.k==="xform")return setCursor(drag.m==="rot"?"grabbing":RESIZE_CURSOR[drag.name]);
      if(x===undefined)return setCursor("default");
      const h=sel.size?handleAt(x,y):null;
      if(h)return setCursor(RESIZE_CURSOR[h[0]]);
      const over=(selBox&&x>=selBox[0]&&x<=selBox[2]&&y>=selBox[1]&&y<=selBox[3])||els.some(e=>hitSelect(e,x,y));
      return setCursor(over?"move":"default")}
    setCursor(cursor);
  }
  function configureInput(){
    cursor=penCursor(S.cursorShape,S.cursorSize);
    updateCursor();
  }
  function moveRing(e){
    if(!ring)return;
    if(tool!=="eraser"||(e&&e.pointerType==="touch")){ring.style.display="none";return}
    ring.style.display="block";ring.style.width=ring.style.height=(2*ER)+"px";
    ring.style.transform="translate("+(e.clientX-ER)+"px,"+(e.clientY-ER)+"px)";
  }

  /* ---- pointer input (mouse, touch, stylus) ---- */
  const world=e=>{sync();return[(e.clientX-view.x)/view.z,(e.clientY-view.y)/view.z]};
  const rawPressure=e=>Number.isFinite(e.pressure)?clamp(e.pressure,0,1):.5;
  const busy=b=>{if(hooks.busy)hooks.busy(b)};
  const capture=id=>{try{top.setPointerCapture(id)}catch(_){}};
  const release=id=>{if(top.hasPointerCapture(id))top.releasePointerCapture(id)};
  const resetTouches=()=>{
    const ids=[...touches.keys()];touches.clear();touchStarted=false;
    for(const id of ids)release(id);
  };
  function moveTouch(e){
    const point=touches.get(e.pointerId);
    if(!point)return;
    const pair=[...touches.values()];
    const other=pair.find(p=>p!==point);
    const dx=e.clientX-point.x,dy=e.clientY-point.y;
    if(!other&&!touchStarted&&Math.hypot(dx,dy)<6)return;
    touchStarted=true;
    if(docMode){scrollBy(-dx/(other?2:1),-dy/(other?2:1))}
    else if(other){
      const cx=(point.x+other.x)/2,cy=(point.y+other.y)/2;
      const distance=Math.hypot(point.x-other.x,point.y-other.y);
      const nextDistance=Math.hypot(e.clientX-other.x,e.clientY-other.y);
      const z=clamp(view.z*Math.max(1,nextDistance)/Math.max(1,distance),ZMIN,ZMAX);
      view.x=cx+dx/2-(cx-view.x)*z/view.z;
      view.y=cy+dy/2-(cy-view.y)*z/view.z;
      view.z=z;
    }else{view.x+=dx;view.y+=dy}
    point.x=e.clientX;point.y=e.clientY;
    if(!docMode&&!touchFrame)touchFrame=requestAnimationFrame(()=>{touchFrame=0;redraw()});
  }
  configureInput();
  top.addEventListener("pointerdown",e=>{
    const pen=e.pointerType==="pen", touch=e.pointerType==="touch";
    if(touch&&(owner||performance.now()-lastPen<120)){e.preventDefault();return}
    if(touch&&S.touchMode!=="ink"){
      e.preventDefault();
      if(touches.size<2){touches.set(e.pointerId,{x:e.clientX,y:e.clientY});capture(e.pointerId)}
      return;
    }
    if(touch&&!e.isPrimary)return;
    if(!pen&&e.button>0&&e.button!==1)return;
    if(owner){
      if(!pen||owner.type!=="touch")return;
      finish(true);
    }
    if(pen){lastPen=performance.now();resetTouches()}
    if(touches.size)return;
    if(touchFrame){cancelAnimationFrame(touchFrame);touchFrame=0;redraw()}
    owner={id:e.pointerId,type:e.pointerType};
    capture(e.pointerId);
    const xy=world(e),x=xy[0],y=xy[1];
    if(!docMode&&(e.button===1||tool==="hand"||space)){drag={k:"pan",sx:e.clientX-view.x,sy:e.clientY-view.y};updateCursor();return}
    busy(true);
    if(tool==="eraser"){drag={k:"erase",snap:els};erase(x,y);return}
    if(tool==="select"){startSelect(e,x,y);return}
    const w=(tool==="hl"?Math.min(80,width*5):width)/view.z;   // on-screen thickness stays what you picked, at any zoom
    const usePressure=e.pointerType==="pen"&&S.pressure>0&&tool==="pen";
    const raw=rawPressure(e);
    const id=newId();
    drag={k:"draw",el:(tool==="pen"||tool==="hl")
      ?{id:id,t:"pen",hl:tool==="hl",c:color,w:w,pen:usePressure,ps:usePressure?S.pressure:0,p:[[x,y,raw||.5,raw]]}
      :{id:id,t:tool,c:color,w:width/view.z,p:[[x,y],[x,y]]}};
  });
  function startSelect(e,x,y){
    const h=sel.size?handleAt(x,y):null;
    if(h){
      if(h[0]==="rot"){const cx=(selBox[0]+selBox[2])/2,cy=(selBox[1]+selBox[3])/2;drag={k:"xform",m:"rot",cx:cx,cy:cy,a0:Math.atan2(h[2]-cy,h[1]-cx),T:null}}
      else{const an=anchorOf(h[0]);drag={k:"xform",m:"scale",name:h[0],ax:an[0],ay:an[1],hx:h[1],hy:h[2],T:null}}
      redraw(sel);updateCursor();return}
    const found=els.slice().reverse().find(el=>hitSelect(el,x,y));
    const inBox=selBox&&sel.size&&x>=selBox[0]&&x<=selBox[2]&&y>=selBox[1]&&y<=selBox[3];
    if(found){
      if(e.shiftKey&&sel.has(found.id)){sel.delete(found.id);updateSel();return}
      if(e.shiftKey)sel.add(found.id);else if(!sel.has(found.id))sel=new Set([found.id]);
    }else if(!inBox){
      drag={k:"marquee",x0:x,y0:y,x1:x,y1:y,add:e.shiftKey,base:e.shiftKey?new Set(sel):new Set()};
      if(!e.shiftKey)sel=new Set();updateSel();return}
    updateSel();drag={k:"move",x0:x,y0:y,dx:0,dy:0};redraw(sel);updateCursor();
  }
  top.addEventListener("pointermove",e=>{
    if(e.pointerType==="touch"&&(!owner||e.pointerId!==owner.id)){moveTouch(e);return}
    if((owner&&e.pointerId!==owner.id)||touches.size)return;
    moveRing(e);
    if(!drag){const xy=world(e);updateCursor(xy[0],xy[1]);return}
    if(e.pointerType==="mouse"&&e.buttons===0){finish();return}   // mouse only: stylus drivers often report buttons=0 while touching
    const d=drag;
    if(d.k==="pan"){view.x=e.clientX-d.sx;view.y=e.clientY-d.sy;redraw();return}
    const xy=world(e),x=xy[0],y=xy[1];
    if(d.k==="erase"){erase(x,y);return}
    if(d.k==="draw"){
      const evs=e.getCoalescedEvents?e.getCoalescedEvents():[];
      for(const q of evs.length?evs:[e]){const w=world(q);
        if(d.el.t==="pen"){const last=d.el.p[d.el.p.length-1],raw=rawPressure(q),pr=raw||.5,sm=last[2]===undefined?pr:last[2]*.55+pr*.45;d.el.p.push([w[0],w[1],sm,raw])}
        else d.el.p[1]=[w[0],w[1]]}
    }else if(d.k==="move"){d.dx=x-d.x0;d.dy=y-d.y0}
    else if(d.k==="marquee"){d.x1=x;d.y1=y}
    else if(d.k==="xform"){
      if(d.m==="rot"){let th=Math.atan2(y-d.cy,x-d.cx)-d.a0;if(e.shiftKey)th=Math.round(th/(Math.PI/12))*(Math.PI/12);d.T={k:"r",cx:d.cx,cy:d.cy,th:th}}
      else{
        const dx=d.hx-d.ax,dy=d.hy-d.ay,rx=dx?(x-d.ax)/dx:1,ry=dy?(y-d.ay)/dy:1;let sx=1,sy=1;
        if(d.name.length===2){if(e.shiftKey){sx=rx;sy=ry}else sx=sy=Math.max(rx,ry)}
        else if(d.name==="n"||d.name==="s")sy=ry;else sx=rx;
        d.T={k:"s",ax:d.ax,ay:d.ay,sx:Math.max(.03,sx),sy:Math.max(.03,sy)}}
    }
    renderTop();
  });
  function finish(discard=false){
    const pointer=owner;owner=null;
    if(pointer){
      if(pointer.type==="pen")lastPen=performance.now();
      release(pointer.id);busy(false);
    }
    if(!drag)return;
    const d=drag;drag=null;
    if(discard){if(d.k==="erase")els=d.snap;redraw();updateSel();updateCursor();return}
    if(d.k==="erase"){if(els!==d.snap){undo.push(d.snap);redo=[]}}
    else if(d.k==="draw"){
      const el=d.el;
      if(el.t==="pen"||Math.hypot(el.p[1][0]-el.p[0][0],el.p[1][1]-el.p[0][1])*view.z>=3){commit(els.concat([el]));applyView(bctx);drawEl(bctx,el,isDark())}
    }else if(d.k==="move"){
      if(Math.hypot(d.dx,d.dy)*view.z>=1)commit(els.map(e=>sel.has(e.id)?shift(e,d.dx,d.dy):e));
      redraw();
    }else if(d.k==="xform"){
      if(d.T)commit(els.map(e=>sel.has(e.id)?xf(e,d.T):e));
      redraw();
    }else if(d.k==="marquee"&&Math.hypot(d.x1-d.x0,d.y1-d.y0)*view.z>3){
      const x0=Math.min(d.x0,d.x1),x1=Math.max(d.x0,d.x1),y0=Math.min(d.y0,d.y1),y1=Math.max(d.y0,d.y1),s=new Set(d.base);
      for(const e of els)if(samplePts(e).some(q=>q[0]>=x0&&q[0]<=x1&&q[1]>=y0&&q[1]<=y1))s.add(e.id);
      sel=s}
    updateSel();updateCursor();
  }
  function endPointer(e){
    if(touches.delete(e.pointerId)&&!touches.size)touchStarted=false;
    if(owner&&e.pointerId===owner.id)finish();
  }
  ["pointerup","pointercancel","lostpointercapture"].forEach(n=>top.addEventListener(n,endPointer));
  top.addEventListener("pointerleave",()=>{if(ring)ring.style.display="none"});
  top.addEventListener("contextmenu",e=>e.preventDefault());
  addEventListener("blur",()=>{space=false;resetTouches();finish()});
  if(docMode)addEventListener("scroll",()=>redraw(),{passive:true});
  addEventListener("resize",resize);

  /* ---- zoom / fit (blackboard) ---- */
  function zoomAt(cx,cy,nz){nz=clamp(nz,ZMIN,ZMAX);view.x=cx-(cx-view.x)*nz/view.z;view.y=cy-(cy-view.y)*nz/view.z;view.z=nz;redraw()}
  function fit(){
    const list=sel.size?selected():els;
    if(!list.length){view.x=0;view.y=0;view.z=1;redraw();return}
    const b=bounds(list),w=b[2]-b[0],h=b[3]-b[1],z=clamp(Math.min(innerWidth/w,innerHeight/h)*.85,ZMIN,ZMAX);
    view.z=z;view.x=innerWidth/2-(b[0]+w/2)*z;view.y=innerHeight/2-(b[1]+h/2)*z;redraw()}
  if(!docMode)top.addEventListener("wheel",e=>{
    e.preventDefault();
    if(owner||touches.size)return;
    if(e.ctrlKey||e.metaKey)zoomAt(e.clientX,e.clientY,view.z*Math.exp(-e.deltaY*(e.deltaMode?.05:.0025)));
    else{view.x-=e.deltaX;view.y-=e.deltaY;redraw()}
  },{passive:false});

  /* ---- public API ---- */
  function paste(groups){
    finish();sync();
    const gap=24;
    let left=0,height=0;
    const positioned=groups.map(group=>{
      const [x0,y0,x1,y1]=bounds(group);
      const dx=left-x0;
      left+=x1-x0+gap;
      height=Math.max(height,y1-y0);
      return {group,dx,dy:-y0};
    });
    const x=(innerWidth/2-view.x)/view.z-(left-gap)/2;
    const y=(innerHeight/2-view.y)/view.z-height/2;
    const strokes=positioned.flatMap(({group,dx,dy})=>group.map(stroke=>{
      const placed=shift(stroke,x+dx,y+dy);
      placed.id=newId();
      return placed;
    }));
    if(!strokes.length)return;
    commit(els.concat(strokes));
    tool="select";sel=new Set(strokes.map(stroke=>stroke.id));redraw();updateSel();
  }
  const recolor=f=>{if(sel.size){commit(els.map(e=>sel.has(e.id)?Object.assign({},e,f(e)):e));redraw();updateSel()}};
  return{
    ZMIN:ZMIN,ZMAX:ZMAX,view:view,drawEl:drawEl,bounds:bounds,redraw:redraw,resize:resize,finish:finish,
    undo:doUndo,redo:doRedo,clear:doClear,delSel:delSel,zoomAt:zoomAt,fit:fit,paste:paste,
    get tool(){return tool},get color(){return color},get width(){return width},get hasSel(){return sel.size>0},
    setTool(t){if(tool==="select"&&t!=="select"){sel=new Set();updateSel()}tool=t;if(ring&&t!=="eraser")ring.style.display="none";updateCursor();renderTop()},
    setColor(c,final){color=c;if(final)recolor(()=>({c:c}))},
    setWidth(w){width=w},
    applyWidthToSelection(){recolor(e=>({w:(e.hl?Math.min(80,width*5):width)/view.z}))},
    setSpace(b){space=b},
    selectAll(){tool="select";sel=new Set(els.map(e=>e.id));updateSel();updateCursor()},
    deselect(){sel=new Set();updateSel()},
    hideSel(b){showSel=!b;renderTop()},
    list(all){return !all&&sel.size?selected():els},
    dump(){return els.length?JSON.stringify(els):""},
    load(j){resetTouches();finish(true);undo=[];redo=[];sel=new Set();try{els=j?JSON.parse(j):[]}catch(_){els=[]}for(const e of els)e.id=newId();redraw();updateSel()},
    nudge(dx,dy){view.x+=dx;view.y+=dy;redraw()},
    updateCursor:updateCursor,configureInput:configureInput,
    endInput(){resetTouches();finish()}
  };
}

return{P:P,svg:svg,el:el,clamp:clamp,CSS:CSS,localizer:localizer,installTips:installTips,makePicker:makePicker,makeWidthControl:makeWidthControl,engine:engine,hsv2hex:hsv2hex,hex2hsv:hex2hsv};
})();
