import{f as t}from"../chunks/fetcher.ASb0Z7gL.js";import{L as l}from"../chunks/layout.CknYAKw6.js";const o=!0,r=!1,n="never",s=async()=>{const{data:e}=await t("/api/method/dinks.api.get_session");return e.csrf_token&&(window.csrf_token=e.csrf_token),{data:e}},c=Object.freeze(Object.defineProperty({__proto__:null,load:s,prerender:o,ssr:r,trailingSlash:n},Symbol.toStringTag,{value:"Module"}));export{l as component,c as universal};
