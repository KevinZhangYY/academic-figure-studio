import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as geometry from '../web/geometry.js';
function editor(){
 const handlers={};
 const canvas={getContext:()=>({}),addEventListener:(name,fn)=>handlers[name]=fn,setPointerCapture(){},getBoundingClientRect:()=>({left:0,top:0,width:1000,height:1000*130/180}),style:{}};
 const sandbox=vm.createContext({...geometry,structuredClone,document:{getElementById:()=>canvas}});
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8').replace(/^import .*\r?\n/,'').split('function removeSelected(')[0];
 vm.runInContext(source+`
 render=()=>{};updateInspector=()=>{};changed=()=>{};status=()=>{};
 state.assets=[{id:'asset',width:1000,cropY:800}];
 state.panels=[{id:'a',sourceId:'asset',x:100,y:100,w:100},{id:'b',sourceId:'asset',x:300,y:100,w:100},{id:'c',sourceId:'asset',x:700,y:100,w:100}];
 globalThis.snapshot=()=>JSON.stringify({panels:state.panels,ids:[...selectedIds],selected,history:history.length});
 globalThis.pick=ids=>setSelection(ids);
 globalThis.addInset=()=>state.panels.push({id:'inset',sourceId:'asset',parentId:'a',x:110,y:110,w:40,roi:{x:0,y:0,w:100,h:100}});
 `,sandbox);
 return {fire:(name,x,y,extra={})=>handlers[name]({clientX:x,clientY:y,pointerId:1,...extra}),get:()=>JSON.parse(sandbox.snapshot()),pick:sandbox.pick,addInset:sandbox.addInset};
}
for(const reverse of [false,true])test(`diagonal marquee ${reverse?'reverse':'forward'} selects and moves multiple panels`,()=>{
 const e=editor(),start=reverse?[450,220]:[50,50],end=reverse?[50,50]:[450,220];
 e.fire('pointerdown',...start);e.fire('pointermove',...end);e.fire('pointerup',...end);
 assert.deepEqual(e.get().ids.sort(),['a','b']);assert.equal(e.get().history,0);
 e.fire('pointerdown',130,130);e.fire('pointermove',150,160);e.fire('pointerup',150,160);
 assert.deepEqual(e.get().panels.map(p=>[p.x,p.y]),[[120,130],[320,130],[700,100]]);
});
test('shift marquee adds to selection and cancel preserves objects and selection',()=>{
 const e=editor();e.pick(['c']);
 e.fire('pointerdown',50,50,{shiftKey:true});e.fire('pointermove',450,220);e.fire('pointerup',450,220);
 assert.deepEqual(e.get().ids.sort(),['a','b','c']);
 const before=e.get();e.fire('pointerdown',20,20);e.fire('pointermove',40,40);e.fire('pointercancel',40,40);
 assert.deepEqual(e.get(),before);
 e.fire('pointerdown',20,20);e.fire('pointerup',20,20);assert.deepEqual(e.get().ids,[]);
});
test('inset stays put when only its parent is marquee-selected',()=>{
 const e=editor();e.addInset();e.fire('pointerdown',50,50);e.fire('pointermove',450,220);e.fire('pointerup',450,220);
 assert.deepEqual(e.get().ids.sort(),['a','b']);
 e.fire('pointerdown',170,130);e.fire('pointermove',190,160);e.fire('pointerup',190,160);
 assert.deepEqual(e.get().panels.map(p=>[p.x,p.y]),[[120,130],[320,130],[700,100],[110,110]]);
});

test('multi-select drag snaps group bottom to another panel top',()=>{
 const e=editor();
 e.fire('pointerdown',50,50);e.fire('pointermove',450,220);e.fire('pointerup',450,220);
 assert.deepEqual(e.get().ids.sort(),['a','b']);
 e.fire('pointerdown',130,130);e.fire('pointermove',130,200);e.fire('pointerup',130,200);
 const panels=e.get().panels;
 assert.deepEqual([panels[0].x,panels[0].y],[100,170]);
 assert.deepEqual([panels[1].x,panels[1].y],[300,170]);
 assert.deepEqual([panels[2].x,panels[2].y],[700,100]);
});