import"./index.De_1-CT6.js";const k="https://dinkclub.erpera.io";async function x(e,T={},b=fetch){var i,y,h,n,u,s,g,w;typeof e=="string"&&(e=new URL(e,k));const{body:c,formBody:a,...p}=T,r=new Headers(p.headers);r.has("Content-Type")||(a&&typeof a=="string"?r.set("Content-Type","application/x-www-form-urlencoded"):c&&r.set("Content-Type","application/json")),r.set("Accept","application/json"),r.set("x-frappe-csrf-token",(globalThis==null?void 0:globalThis.csrf_token)||"");const f={method:"GET",headers:r,credentials:"include",...p};(c||a)&&(f.body=a||JSON.stringify(c),console.log("options.body",{body:c,formBody:a}));let o;try{o=await b(e,f)}catch(l){return console.error("Fetch Error",e,l),{data:null,error:"Failed connecting",status:0}}let d="",t;try{t=await o.json()}catch{}if(!o.ok){const l=((w=(g=(s=(u=(n=(h=(y=(i=t==null?void 0:t.exception)==null?void 0:i.split)==null?void 0:y.call(i,":"))==null?void 0:h[0])==null?void 0:n.split)==null?void 0:u.call(n,"."))==null?void 0:s.reverse)==null?void 0:g.call(s))==null?void 0:w[0])||(t==null?void 0:t.exc_type)||"Fetch Error";console.error(l,e,o.status,t),d=t||""}return{data:o.ok?(t==null?void 0:t.data)??(t==null?void 0:t.message)??t:null,error:d,status:o.status}}export{k as P,x as f};
