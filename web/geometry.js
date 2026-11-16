export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const factor=u=>u==='nm'?1:u==='mm'?1e6:1000;
export function niceLength(n){if(!(n>0))return 1;const e=10**Math.floor(Math.log10(n));return [5,2,1].map(v=>v*e).find(v=>v<=n)||e/2;}
export function formatLength(nm){let unit=nm>=1e6?'mm':nm>=1000?'µm':'nm';return {value: +(nm/factor(unit)).toPrecision(4),unit};}
export function normalizeRect(a,b){return {x:Math.min(a.x,b.x),y:Math.min(a.y,b.y),w:Math.abs(a.x-b.x),h:Math.abs(a.y-b.y)};}
export function sourceCrop(panel,asset){return panel.roi?[panel.roi.x,panel.roi.y,panel.roi.w,panel.roi.h]:[0,0,asset.width,asset.cropY];}
export function panelHeight(panel,asset){const c=sourceCrop(panel,asset);return panel.w*c[3]/c[2];}
export function scalePixels(lengthNm,nmPerPx,displayWidth,sourceWidth){return lengthNm/nmPerPx*displayWidth/sourceWidth;}
export function scaleBarDisplay(panel,asset,maxWidth=panel.w-30){
 const crop=sourceCrop(panel,asset),automatic=scalePixels(panel.barNm,asset.nmPerPx,panel.w,crop[2]);
 const custom=Number.isFinite(panel.barWidth)&&panel.barWidth>0;
 const pixels=custom?clamp(panel.barWidth,4,Math.max(4,maxWidth)):automatic;
 return {pixels,auto:automatic,physicalNm:custom?pixels*asset.nmPerPx*crop[2]/panel.w:panel.barNm};
}
// Annotation dimensions are figure-space values, independent of image/ROI size.
export function scaleBarStyle(panel,fontSize=20){
 return {fontSize:Number.isFinite(panel.barFontSize)&&panel.barFontSize>=2?panel.barFontSize:fontSize*.72,
  thickness:Number.isFinite(panel.barThickness)&&panel.barThickness>=1?panel.barThickness:Math.max(2.5,fontSize*.16)};
}
export function scaleBarLayout(panel,asset,fontSize,textWidth,labelHeight=0){
 const spec=scaleBarDisplay(panel,asset),style=scaleBarStyle(panel,fontSize);
 const edge=panel.barOutline!==false?1.3:0,textEdge=panel.barOutline!==false?1.1:0;
 const margin=15,gap=4,textHeight=style.fontSize*1.25;
 const w=Math.max(spec.pixels+2*edge,textWidth+2*textEdge);
 const h=textHeight+2*textEdge+gap+style.thickness+2*edge;
 const right=panel.barPosition.endsWith('r'),bottom=panel.barPosition.startsWith('b');
 const x=right?panel.x+panel.w-margin-w:panel.x+margin;
 const y=bottom?panel.y+panelHeight(panel,asset)-margin-h:panel.y+margin+labelHeight;
 const center=x+w/2,barY=y+h-edge-style.thickness;
 return {...spec,...style,block:{x,y,w,h},barX:center-spec.pixels/2,barY,textX:center,textY:y+textEdge,
  fits:w+2*margin<=panel.w&&h+2*margin+labelHeight<=panelHeight(panel,asset)};
}
export function sourcePoint(point,panel,asset){const c=sourceCrop(panel,asset),s=panel.w/c[2];return {x:clamp((point.x-panel.x)/s+c[0],c[0],c[0]+c[2]),y:clamp((point.y-panel.y)/s+c[1],c[1],c[1]+c[3])};}
export function connectorLines(roi,inset){const rc={x:roi.x+roi.w/2,y:roi.y+roi.h/2},ic={x:inset.x+inset.w/2,y:inset.y+inset.h/2};const dx=ic.x-rc.x,dy=ic.y-rc.y;if(Math.abs(dx)>Math.abs(dy)){const rx=dx>=0?roi.x+roi.w:roi.x,ix=dx>=0?inset.x:inset.x+inset.w;return [[rx,roi.y,ix,inset.y],[rx,roi.y+roi.h,ix,inset.y+inset.h]];}const ry=dy>=0?roi.y+roi.h:roi.y,iy=dy>=0?inset.y:inset.y+inset.h;return [[roi.x,ry,inset.x,iy],[roi.x+roi.w,ry,inset.x+inset.w,iy]];}
export function snapAlignment(moving,others,threshold=8){
 const snapped={x:moving.x,y:moving.y},guides=[],matches=[];
 for(const axis of ['x','y']){
  const vertical=axis==='x',offsets=vertical?[[0,'left'],[moving.w,'right']]:[[0,'top'],[moving.h,'bottom']];
  let best=null;
  for(const other of others){
   const otherOffsets=vertical?[[other.x,'left','edge'],[other.x+other.w,'right','edge']]
                              :[[other.y,'top','edge'],[other.y+other.h,'bottom','edge']];
   for(const [moveOffset,moveKind] of offsets)for(const [otherValue,otherKind] of otherOffsets){
    const shift=otherValue-(moving[axis]+moveOffset),distance=Math.abs(shift);
    if(distance>threshold)continue;
    if(!best||distance<best.distance)best={shift,distance,at:otherValue,moveKind,otherKind,other};
   }
  }
  if(!best)continue;
  snapped[axis]+=best.shift;
  matches.push({vertical,best});
 }
 // Both axes must settle before guides are extended over the final bounds.
 for(const {vertical,best} of matches){
  const low=vertical?Math.min(best.other.y,snapped.y):Math.min(best.other.x,snapped.x);
  const high=vertical?Math.max(best.other.y+best.other.h,snapped.y+moving.h):Math.max(best.other.x+best.other.w,snapped.x+moving.w);
  guides.push({axis:vertical?'vertical':'horizontal',at:best.at,from:low,to:high,moveKind:best.moveKind,otherKind:best.otherKind});
 }
 return {bounds:snapped,guides};
}
