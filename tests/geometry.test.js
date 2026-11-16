import test from 'node:test';import assert from 'node:assert/strict';import {sourceCrop,scalePixels,sourcePoint,connectorLines,formatLength,niceLength,snapAlignment,scaleBarDisplay,scaleBarStyle,scaleBarLayout} from '../web/geometry.js';
test('scale bars preserve physical length through resizing and ROI zoom',()=>{assert.equal(scalePixels(2000,10,500,1000),100);assert.equal(scalePixels(2000,10,250,1000),50);assert.equal(scalePixels(2000,10,500,250),400)});
test('source ROI maps canvas coordinates to original pixels',()=>{const a={width:1000,cropY:600};const p={x:30,y:50,w:500};assert.deepEqual(sourcePoint({x:280,y:200},p,a),{x:500,y:300});assert.deepEqual(sourcePoint({x:900,y:900},p,a),{x:1000,y:600});assert.deepEqual(sourceCrop({...p,roi:{x:200,y:100,w:150,h:80}},a),[200,100,150,80])});
test('connectors follow near edges in four directions',()=>{const r={x:100,y:100,w:20,h:20};assert.deepEqual(connectorLines(r,{x:200,y:100,w:50,h:50})[0],[120,100,200,100]);assert.deepEqual(connectorLines(r,{x:0,y:100,w:50,h:50})[0],[100,100,50,100]);assert.deepEqual(connectorLines(r,{x:100,y:200,w:50,h:50})[0],[100,120,100,200]);assert.deepEqual(connectorLines(r,{x:100,y:0,w:50,h:50})[0],[100,100,100,50]);});
test('moving panels snap to the nearest edge and draw its alignment guide',()=>{
 const result=snapAlignment({x:96,y:40,w:120,h:80},[{x:100,y:100,w:160,h:120}],5);
 assert.deepEqual(result.bounds,{x:100,y:40});
 assert.equal(result.guides.length,1);assert.equal(result.guides[0].axis,'vertical');assert.equal(result.guides[0].at,100);
 assert.deepEqual([result.guides[0].from,result.guides[0].to],[40,220]);
});
test('horizontal and vertical alignment snap independently',()=>{
 const result=snapAlignment({x:98,y:226,w:100,h:50},[{x:100,y:230,w:140,h:70}],6);
 assert.deepEqual(result.bounds,{x:100,y:230});assert.deepEqual(result.guides.map(g=>g.axis).sort(),['horizontal','vertical']);
});
test('alignment does not snap beyond the interaction threshold',()=>{
 const result=snapAlignment({x:110,y:100,w:120,h:80},[{x:100,y:160,w:160,h:120}],6);
 assert.deepEqual(result.bounds,{x:110,y:100});assert.deepEqual(result.guides,[]);
});
test('scale bars use custom display size while preserving calibrated physical length',()=>{
 const asset={width:600,cropY:500,nmPerPx:10};const panel={x:0,y:0,w:300,barNm:100};
 assert.equal(scaleBarDisplay(panel,asset).pixels,5);assert.equal(scaleBarDisplay(panel,asset).physicalNm,100);
 const custom={...panel,barWidth:90};const shown=scaleBarDisplay(custom,asset);
 assert.equal(shown.pixels,90);assert.equal(shown.physicalNm,1800);
});
test('scale formatting and automatic lengths',()=>{assert.deepEqual(formatLength(2000),{value:2,unit:'µm'});assert.deepEqual(formatLength(500),{value:500,unit:'nm'});assert.deepEqual(formatLength(1e6),{value:1,unit:'mm'});assert.equal(niceLength(987),500)});

test('inset scale typography stays constant while physical bar scales with the image',()=>{
 const a={width:1000,cropY:800,nmPerPx:10};
 const p={x:100,y:80,w:240,roi:{x:0,y:0,w:200,h:180},barNm:500,barPosition:'br'};
 const before=scaleBarLayout(p,a,20,52),after=scaleBarLayout({...p,w:120},a,20,52);
 assert.equal(before.fontSize,20*.72);assert.equal(after.fontSize,before.fontSize);
 assert.equal(after.thickness,before.thickness);
 assert.equal(after.pixels,before.pixels/2);assert.equal(after.physicalNm,500);
 assert.equal(scaleBarStyle({...p,barFontSize:22,barThickness:5},20).fontSize,22);
 assert.equal(scaleBarStyle({...p,w:80,barFontSize:22,barThickness:5},20).thickness,5);
});
test('all four scale anchors position the full label and bar block inside the panel',()=>{
 const a={width:1000,cropY:800,nmPerPx:10};
 for(const barPosition of ['br','bl','tr','tl']){
  const p={x:80,y:100,w:180,roi:{x:0,y:0,w:200,h:180},barNm:500,barPosition};
  const q=scaleBarLayout(p,a,20,70,barPosition.startsWith('t')?25:0);
  assert.ok(q.fits);assert.equal(q.textX,q.barX+q.pixels/2);
  assert.ok(q.textX-35>=p.x+15);assert.ok(q.textX+35<=p.x+p.w-15);
  assert.ok(q.textY+q.fontSize*1.25<q.barY);
  if(barPosition.startsWith('b'))assert.ok(Math.abs(q.barY+q.thickness+1.3-(p.y+162-15))<1e-9);
  if(barPosition.endsWith('r'))assert.equal(q.block.x+q.block.w,p.x+p.w-15);
  else assert.equal(q.block.x,p.x+15);
 }
});
test('oversized annotations are reported without silently shrinking the font',()=>{
 const q=scaleBarLayout({x:0,y:0,w:50,barNm:200,barPosition:'br'}, {width:100,cropY:100,nmPerPx:10},20,70);
 assert.equal(q.fits,false);assert.equal(q.fontSize,20*.72);
});
