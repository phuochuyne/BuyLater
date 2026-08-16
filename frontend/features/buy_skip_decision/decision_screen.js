(() => {
'use strict';
const config={"actions":[{"authentication":"required","function_id":"capability_buy_skip_decision_c984506c.function.get_decision_screen_data","id":"capability_buy_skip_decision_c984506c.screen-action.load_decision_data","method":"GET","request_schema":{"properties":{"item_id":{"description":"UUID of the item to display decision screen for","format":"uuid","type":"string"}},"required":["item_id"],"type":"object"},"response_schema":{"properties":{"already_decided":{"description":"Whether user has already made a decision for this item","type":"boolean"},"current_total_saved":{"description":"User's current cumulative savings total","format":"decimal","type":"number"},"item_id":{"format":"uuid","type":"string"},"item_link":{"description":"Product URL from dependency feature","format":"uri","type":"string"},"item_name":{"description":"Item name from dependency feature","type":"string"},"item_price":{"description":"Item price from dependency feature","format":"decimal","type":"number"}},"required":["item_id","item_name","item_price","item_link","current_total_saved","already_decided"],"type":"object"},"route":"/api/capability_buy_skip_decision_c984506c/items/{item_id}/decision","success_route":null},{"authentication":"required","function_id":"capability_buy_skip_decision_c984506c.function.record_buy_decision","id":"capability_buy_skip_decision_c984506c.screen-action.tap_buy","method":"POST","request_schema":{"properties":{"item_id":{"description":"UUID of the item being decided on","format":"uuid","type":"string"},"item_price":{"description":"Price of the item at decision time","format":"decimal","minimum":0,"type":"number"}},"required":["item_id","item_price"],"type":"object"},"response_schema":{"properties":{"decided_at":{"format":"date-time","type":"string"},"decision_id":{"format":"uuid","type":"string"},"decision_type":{"enum":["buy"],"type":"string"},"item_id":{"format":"uuid","type":"string"},"product_link":{"description":"URL to open in browser/external app","format":"uri","type":"string"}},"required":["decision_id","item_id","decision_type","decided_at","product_link"],"type":"object"},"route":"/api/capability_buy_skip_decision_c984506c/items/{item_id}/decide/buy","success_route":"/decision/:item_id/skipped"},{"authentication":"required","function_id":"capability_buy_skip_decision_c984506c.function.record_skip_decision","id":"capability_buy_skip_decision_c984506c.screen-action.tap_skip","method":"POST","request_schema":{"properties":{"item_id":{"description":"UUID of the item being decided on","format":"uuid","type":"string"},"item_price":{"description":"Price of the item to add to savings total","format":"decimal","minimum":0,"type":"number"}},"required":["item_id","item_price"],"type":"object"},"response_schema":{"properties":{"decided_at":{"format":"date-time","type":"string"},"decision_id":{"format":"uuid","type":"string"},"decision_type":{"enum":["skip"],"type":"string"},"item_id":{"format":"uuid","type":"string"},"new_total_saved":{"description":"Updated cumulative savings total after this skip","format":"decimal","type":"number"},"price_saved":{"description":"Amount added to savings from this skip","format":"decimal","type":"number"}},"required":["decision_id","item_id","decision_type","decided_at","price_saved","new_total_saved"],"type":"object"},"route":"/api/capability_buy_skip_decision_c984506c/items/{item_id}/decide/skip","success_route":"/decision/:item_id/skipped"}],"screen_route":"/decision/:item_id"};
const actionById=new Map(config.actions.map(action=>[action.id,action]));
const routeNames=template=>[...String(template||'').matchAll(/\{([A-Za-z_]\w*)\}/g)].map(match=>match[1]);
const previewValue=name=>name.endsWith('_id')||name==='id'?'example-id':'example';
const routeValues=()=>{
  const names=routeNames(config.screen_route);
  const pattern='^'+String(config.screen_route||'/').replace(/[.*+?^${}()|[\]\\]/g,'\\$&').replace(/\\\{([A-Za-z_]\w*)\\\}/g,'([^/]+)')+'$';
  const match=location.pathname.match(new RegExp(pattern));
  return Object.fromEntries(names.map((name,index)=>[name,match?decodeURIComponent(match[index+1]||''):previewValue(name)]));
};
const materialize=(template,values)=>String(template||'').replace(/\{([A-Za-z_]\w*)\}/g,(_,name)=>encodeURIComponent(values[name]??previewValue(name)));
const valueAt=(value,path)=>String(path||'').split('.').reduce((current,key)=>current&&typeof current==='object'?current[key]:undefined,value);
const display=value=>value==null?'—':typeof value==='object'?JSON.stringify(value):String(value);
const render=(payload,scope=document)=>scope.querySelectorAll('[data-bind]').forEach(node=>{
  const value=valueAt(payload,node.dataset.bind);
  if(value===undefined)return;
  if(Array.isArray(value)){
    const template=node.firstElementChild?.cloneNode(true);node.replaceChildren();
    value.forEach(item=>{if(template){const child=template.cloneNode(true);render(item,child);node.append(child);}else{const child=document.createElement('div');child.className='generated-item';child.textContent=display(item);node.append(child);}});
  }else node.textContent=display(value);
});
const region=(root,name)=>root.querySelector(`[data-${name}-region]`)||document.querySelector(`[data-${name}-region]`);
const show=(root,name,message)=>{const target=region(root,name);if(target){target.hidden=false;if(message)target.textContent=message;}};
const loading=(root,value)=>{root.dataset.loading=String(Boolean(value));root.querySelectorAll('button,input,textarea,select').forEach(node=>node.disabled=Boolean(value));};
const valuesFrom=root=>{const form=root.tagName==='FORM'?root:root.querySelector('form');return form?Object.fromEntries(new FormData(form).entries()):{};};
const coerce=(values,schema)=>Object.fromEntries(Object.entries(values).map(([key,value])=>{const rules=schema?.properties?.[key]||{};if(rules.type==='integer')return[key,Number.parseInt(value,10)];if(rules.type==='number')return[key,Number(value)];if(rules.type==='boolean')return[key,['true','1','on','yes'].includes(String(value).toLowerCase())];return[key,value];}));
const execute=async(root,action)=>{
  const requestSchema=action.request_schema||{};const requestValues=coerce(valuesFrom(root),requestSchema);const values={...routeValues(),...requestValues};let url=materialize(action.route,values);
  for(const name of requestSchema.required||[]){if(requestValues[name]===''||requestValues[name]===undefined){show(root,'error',`${name.replaceAll('_',' ')} is required.`);return;}}
  const pathNames=new Set(routeNames(action.route));const allowed=new Set(Object.keys(requestSchema.properties||{}));const body=Object.fromEntries(Object.entries(requestValues).filter(([key,value])=>allowed.has(key)&&!pathNames.has(key)&&value!==''));
  const headers={Accept:'application/json'};const token=localStorage.getItem('zorentia_access_token');if(action.authentication==='required'&&!token&&!window.__ZORENTIA_PREVIEW__){show(root,'error','Please sign in before using this action.');return;}if(token)headers.Authorization=`Bearer ${token}`;
  const options={method:action.method,headers};
  if(['GET','HEAD'].includes(action.method)){const query=new URLSearchParams(Object.entries(body));if(query.size)url+=`${url.includes('?')?'&':'?'}${query}`;}
  else{headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  loading(root,true);const errorRegion=region(root,'error');if(errorRegion)errorRegion.hidden=true;
  try{const response=await fetch(url,options);const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.message||payload.error||`Request failed (${response.status})`);if(payload.token)localStorage.setItem('zorentia_access_token',payload.token);render(payload,root);show(root,'success');if(action.success_route&&!window.__ZORENTIA_PREVIEW__)location.href=materialize(action.success_route,{...values,...payload});}
  catch(error){show(root,'error',error?.message||'Something went wrong. Please try again.');}
  finally{loading(root,false);}
};
document.querySelectorAll('[data-action-id]').forEach(root=>{
  const action=actionById.get(root.dataset.actionId);if(!action)return;
  if(root.tagName==='FORM')root.addEventListener('submit',event=>{event.preventDefault();execute(root,action);});
  else root.addEventListener('click',event=>{if(event.target.closest('button,[data-trigger]'))execute(root,action);});
  if(['GET','HEAD'].includes(action.method)&&root.dataset.autoload==='true')execute(root,action);
});
})();