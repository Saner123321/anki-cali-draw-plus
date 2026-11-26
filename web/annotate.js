/* Anki-Cali Draw Plus annotation overlay: injected into Anki's reviewer page by annotation.py (after core.js).
   Transparent canvas over the card, toolbar in a shadow root (card CSS can't touch it). */
(function(){
"use strict";
if(window.__caliplus)return;
const C=window.CaliPlusCore,P=C.P,svg=C.svg;

const host=document.createElement("div");
host.style.cssText="position:fixed;left:0;top:0;width:0;height:0;z-index:2147483000";
const root=host.attachShadow({mode:"open"});
root.innerHTML='<style>'+C.CSS+`
#wrap{position:fixed;left:0;top:0;width:0;height:0}
#base,#top{position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;touch-action:none}
#top.live{pointer-events:auto}
#bar{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);flex-wrap:wrap;justify-content:center;max-width:94vw;pointer-events:auto;touch-action:none;z-index:5}
.grip{cursor:move;padding:0 6px;opacity:.5;letter-spacing:-2px}
</style><div id="wrap" class="ad-root"><canvas id="base"></canvas><canvas id="top"></canvas><div id="ring" class="ad-ring"></div><div id="bar" class="ad-isl ad-ui"></div></div>`;
document.body.appendChild(host);
const $=id=>root.getElementById(id),wrap=$("wrap"),bar=$("bar"),top=$("top");

const S={pressure:.7,zen:"writing",zenKey:"",favs:["#e03131","#1971c2","#2f9e44","#f08c00","#9c36b5"]};
const L=C.localizer(S),tr=L.tr;
let live=true,zenHidden=false,busyTimer=null,shown=false;
C.installTips(wrap);

const D=C.engine({base:$("base"),top:top,ring:$("ring"),view:{x:0,y:0,z:1},docMode:true,S:S,inkDark:"#f2f2f2",
  isDark:()=>wrap.classList.contains("dark"),
  accent:()=>getComputedStyle(wrap).getPropertyValue("--ac").trim(),
  hooks:{sel:onSel,busy:onBusy}});

/* ---- toolbar ---- */
function btn(html,tip,fn,cls){const b=C.el("button",cls||"",html);if(tip)L.tip(b,tip);if(fn)b.onclick=fn;bar.appendChild(b);return b}
const sep=()=>bar.appendChild(C.el("div","ad-sep"));
const grip=C.el("div","grip","\u22EE\u22EE");L.tip(grip,"Drag to move this toolbar");bar.appendChild(grip);
let gdrag=null;
grip.addEventListener("pointerdown",e=>{try{grip.setPointerCapture(e.pointerId)}catch(_){}const r=bar.getBoundingClientRect();gdrag=[e.clientX-r.left,e.clientY-r.top]});
grip.addEventListener("pointermove",e=>{if(!gdrag)return;if(e.pointerType==="mouse"&&e.buttons===0){gdrag=null;return}
  Object.assign(bar.style,{transform:"none",bottom:"auto",left:Math.max(0,e.clientX-gdrag[0])+"px",top:Math.max(0,e.clientY-gdrag[1])+"px"})});
["pointerup","pointercancel"].forEach(n=>grip.addEventListener(n,()=>gdrag=null));

const modeBtn=btn(svg(P.pointer),"Interact with the card (click a tool to draw again)",()=>setLive(!live));
function setLive(v){D.endInput();live=v;top.classList.toggle("live",v);modeBtn.classList.toggle("on",!v);
  L.tip(modeBtn,v?"Drawing. Click to interact with the card":"Interacting. Click to draw again");
  if(!v)$("ring").style.display="none"}
sep();
const tb={};
function setTool(t){D.setTool(t);for(const k in tb)tb[k].classList.toggle("on",k===t);if(!live)setLive(true)}
[["select","Select / move / resize / rotate"],["pen","Pen"],["hl","Highlighter"],["line","Line"],["arrow","Arrow"],["rect","Rectangle"],["ellipse","Ellipse"],["eraser","Eraser"]]
 .forEach(([t,h])=>tb[t]=btn(svg(t==="select"?P.move:P[t]),h,()=>setTool(t)));
sep();

/* colours: ink + 5 favourites + spectrum */
const swHost=C.el("div");swHost.style.cssText="display:flex;align-items:center;gap:5px;padding:0 3px";bar.appendChild(swHost);
const same=(a,b)=>String(a).toLowerCase()===String(b).toLowerCase();
function markSwatch(){[...swHost.querySelectorAll(".ad-sw[data-c]")].forEach(b=>b.classList.toggle("on",same(b.getAttribute("data-c"),D.color)))}
function pick(c){D.setColor(c,true);markSwatch()}
function setFavs(f){S.favs=f;renderSwatches();picker.renderFavs();pycmd("caliplus:favs:"+JSON.stringify(f))}
function sbtn(tip,fn,cls){const b=C.el("button",cls);L.tip(b,tip);b.onclick=fn;swHost.appendChild(b);return b}
function renderSwatches(){
  swHost.innerHTML="";
  const ink=sbtn("Default (yellow for highlighter)",()=>pick("auto"),"ad-sw");ink.setAttribute("data-c","auto");ink.style.background="linear-gradient(135deg,#1e1e1e 50%,#ffd43b 50%)";
  S.favs.forEach((c,i)=>{const b=sbtn(tr("Favourite {number} (right-click: replace with the current colour)",{number:i+1}),()=>pick(c),"ad-sw");
    b.setAttribute("data-c",c);b.style.background=c;
    b.oncontextmenu=ev=>{ev.preventDefault();if(D.color!=="auto"&&!same(D.color,c)){const f=S.favs.slice();f[i]=D.color;setFavs(f)}}});
  const sp=sbtn("Colour spectrum - pick any colour, save 5 favourites",()=>picker.toggle(),"ad-sw ad-spec");sp.setAttribute("data-spec","1");
  markSwatch();
}
const picker=C.makePicker({parent:wrap,tr:tr,getColor:()=>D.color,getFavs:()=>S.favs,setFavs:setFavs,
  onPick:(c,final)=>{D.setColor(c,final);markSwatch()},
  place:pop=>{const r=bar.getBoundingClientRect();
    pop.style.left=Math.max(8,Math.min(innerWidth-pop.offsetWidth-8,r.left+r.width/2-pop.offsetWidth/2))+"px";
    pop.style.top=Math.max(8,Math.min(innerHeight-pop.offsetHeight-8,r.top-pop.offsetHeight-10))+"px"}});
renderSwatches();
sep();

/* thickness slider */
const widthControl=C.makeWidthControl(D,L,false,w=>pycmd("caliplus:width:"+w));
bar.appendChild(widthControl.el);
sep();

btn(svg(P.undo),"Undo",D.undo);btn(svg(P.redo),"Redo",D.redo);
const trashBtn=btn(svg(P.trash),"Clear annotations",()=>D.hasSel?D.delSel():D.clear());
const eyeBtn=btn(svg(P.eye),"",()=>api.toggleZen());
sep();
const copyBtn=btn(svg(P.copy)+"Copy","Copy the card with your annotations to the clipboard",()=>pycmd("caliplus:copy"),"pri");
btn(svg(P.gear),"Anki-Cali Draw Plus settings",()=>pycmd("caliplus:settings"));
btn(svg(P.close),"Close annotation mode",()=>{api.hide();pycmd("caliplus:closed")});
function onSel(n){L.tip(trashBtn,n?"Delete selection":"Clear annotations")}

/* ---- zen mode ---- */
const ghost=C.el("button","ad-ghost",svg(P.eye));L.tip(ghost,"Show the tools again");ghost.onclick=()=>api.toggleZen();wrap.appendChild(ghost);
function updateZenTip(){L.tip(eyeBtn,"Zen mode: hide all tools. Bring them back with the faint eye in the corner")}
function applyZen(){wrap.classList.toggle("zen",zenHidden);if(zenHidden)picker.close()}
function onBusy(b){
  if(S.zen!=="writing")return;
  clearTimeout(busyTimer);
  if(b){wrap.classList.add("writing");picker.close()}else busyTimer=setTimeout(()=>wrap.classList.remove("writing"),250);
}

/* ---- API for Python ---- */
function configure(o){
  const zen=S.zen;Object.assign(S,o);
  D.configureInput();
  if("dark" in o){wrap.classList.toggle("dark",!!o.dark);D.redraw()}
  if("penWidth" in o)widthControl.restore(S.penWidth);
  if("strings" in o){L.refresh(wrap);copyBtn.lastChild.nodeValue=tr("Copy")}
  if("favs" in o||"strings" in o){renderSwatches();picker.renderFavs()}
  if("zenKey" in o)updateZenTip();
  if("zen" in o&&o.zen!==zen){zenHidden=S.zen==="toggle";wrap.classList.remove("writing");applyZen()}
}
const api=window.__caliplus={
  show(o){configure(o||{});if(!shown){zenHidden=S.zen==="toggle";shown=true}applyZen();   // re-shows (new card) keep the zen state
    host.style.display="";bar.style.display="flex";setLive(true);D.resize()},
  hide(){D.endInput();picker.close();host.style.display="none"},
  configure:configure,
  setTheme(d){configure({dark:!!d})},
  toggleZen(){zenHidden=!zenHidden;applyZen()},
  clear:D.clear,dump:D.dump,load:D.load,
  prep(){wrap.classList.add("shot");D.hideSel(true);return 1},          // hide toolbar + selection box for a screenshot
  unprep(){wrap.classList.remove("shot");D.hideSel(false);return 1}
};
setTool("pen");setLive(true);D.resize();updateZenTip();
})();
