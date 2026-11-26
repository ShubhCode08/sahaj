// Dependency-free tests of the actual panel-side guard and page action function.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const src = fs.readFileSync(path.join(__dirname,'../extension/panel.js'),'utf8');
const elements = new Map();
const ctx = vm.createContext({document:{getElementById:id=>{if(!elements.has(id))elements.set(id,{});return elements.get(id);},querySelectorAll:()=>[]},window:{addEventListener:()=>{}}});
vm.runInContext(src,ctx);
function test(code){assert.equal(vm.runInContext(code,ctx),true,code);}
test(`allowed('bus',0,{action:'navigate',target:'/demo/bus',value:null})`);
test(`!allowed('bus',0,{action:'navigate',target:'https://example.com',value:null})`);
test(`!allowed('bill',2,{action:'click',target:'payment',value:null})`);
test(`!allowed('bill',1,{action:'fill',target:'consumer-id',value:'real ID'})`);
test(`!allowed('bus',3,{action:'fill',target:'to',value:'Mysuru'})`);
test(`!allowed('scheme',2,{action:'click',target:'submit',value:null})`);
test(`!allowed('compare',0,{action:'click',target:'checkout',value:null})`);
test(`!allowed('__proto__',0,{action:'click',target:'x',value:null})`);
test(`!allowed('bus',-1,{action:'navigate',target:'/demo/bus',value:null})`);
console.log('9 browser-side guard checks passed (Node VM; no real Chrome APIs).');
