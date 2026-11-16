import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as geometry from '../web/geometry.js';

test('render/export scene uses stable typography for old projects and resized insets',()=>{
 // Exercise the actual shared scene builder without browser automation.
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8').replace(/^import .*\r?\n/,'').split('function drawScene(')[0];
 const context={save(){},restore(){},measureText(){return {width:60}}};
 const sandbox=vm.createContext({...geometry,structuredClone,document:{getElementById(){return {getContext(){return context}}}}});
 vm.runInContext(source+`
 state.assets=[{id:'a',width:1000,cropY:800,nmPerPx:10,calibrated:true}];
 state.panels=[{id:'p',sourceId:'a',x:0,y:0,w:400,barNm:2000,showScale:true,barPosition:'br',barColor:'#ffffff'},
 {id:'i',sourceId:'a',parentId:'p',roi:{x:0,y:0,w:200,h:180},x:500,y:100,w:240,barNm:500,showScale:true,barPosition:'br',barColor:'#ffffff'}];
 globalThis.getScene=()=>scene();globalThis.resize=w=>state.panels[1].w=w;
 globalThis.custom=()=>Object.assign(state.panels[1],{barFontSize:24,barThickness:6});
 `,sandbox);
 const labels=sandbox.getScene().filter(e=>e.role==='scale-label');
 assert.equal(labels[0].size,labels[1].size);
 const original=sandbox.getScene().findLast(e=>e.role==='scale-bar');
 sandbox.resize(120);
 const output=sandbox.getScene(),label=output.findLast(e=>e.role==='scale-label'),bar=output.findLast(e=>e.role==='scale-bar');
 assert.equal(label.size,labels[1].size);assert.equal(label.text,'500 nm');
 assert.equal(bar.w,original.w/2);assert.equal(bar.h,original.h);
 assert.ok(label.x+30<=500+120-15);
 assert.ok(Math.abs(bar.y+bar.h+1.3-(100+108-15))<1e-9);
 sandbox.custom();sandbox.resize(180);
 assert.equal(sandbox.getScene().findLast(e=>e.role==='scale-label').size,24);
 assert.equal(sandbox.getScene().findLast(e=>e.role==='scale-bar').h,6);
});
