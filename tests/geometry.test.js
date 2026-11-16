import test from 'node:test';import assert from 'node:assert/strict';import {sourceCrop,scalePixels,sourcePoint,connectorLines,formatLength,niceLength,snapAlignment} from '../web/geometry.js';
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
test('scale formatting and automatic lengths',()=>{assert.deepEqual(formatLength(2000),{value:2,unit:'µm'});assert.deepEqual(formatLength(500),{value:500,unit:'nm'});assert.deepEqual(formatLength(1e6),{value:1,unit:'mm'});assert.equal(niceLength(987),500)});
