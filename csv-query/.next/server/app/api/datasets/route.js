(()=>{var e={};e.id=356,e.ids=[356],e.modules={20399:e=>{"use strict";e.exports=require("next/dist/compiled/next-server/app-page.runtime.prod.js")},30517:e=>{"use strict";e.exports=require("next/dist/compiled/next-server/app-route.runtime.prod.js")},78893:e=>{"use strict";e.exports=require("buffer")},84770:e=>{"use strict";e.exports=require("crypto")},17702:e=>{"use strict";e.exports=require("events")},92048:e=>{"use strict";e.exports=require("fs")},32615:e=>{"use strict";e.exports=require("http")},35240:e=>{"use strict";e.exports=require("https")},98216:e=>{"use strict";e.exports=require("net")},19801:e=>{"use strict";e.exports=require("os")},55315:e=>{"use strict";e.exports=require("path")},76162:e=>{"use strict";e.exports=require("stream")},82452:e=>{"use strict";e.exports=require("tls")},17360:e=>{"use strict";e.exports=require("url")},21764:e=>{"use strict";e.exports=require("util")},71568:e=>{"use strict";e.exports=require("zlib")},93739:()=>{},32017:(e,t,r)=>{"use strict";r.r(t),r.d(t,{originalPathname:()=>h,patchFetch:()=>q,requestAsyncStorage:()=>l,routeModule:()=>d,serverHooks:()=>m,staticGenerationAsyncStorage:()=>x});var s={};r.r(s),r.d(s,{GET:()=>p,dynamic:()=>c});var a=r(49303),i=r(88716),o=r(60670),u=r(87070),n=r(9487);let c="force-dynamic";async function p(){try{await (0,n.a)();let e=await (0,n.i)`
      SELECT 
        id, 
        name, 
        columns, 
        row_count, 
        blob_url, 
        created_at
      FROM datasets
      ORDER BY created_at DESC;
    `;return u.NextResponse.json({datasets:e.rows})}catch(e){return console.error("Error fetching datasets:",e),u.NextResponse.json({error:"Failed to fetch datasets."},{status:500})}}let d=new a.AppRouteRouteModule({definition:{kind:i.x.APP_ROUTE,page:"/api/datasets/route",pathname:"/api/datasets",filename:"route",bundlePath:"app/api/datasets/route"},resolvedPagePath:"C:\\Users\\Ayush Kumar\\Desktop\\Text-to-SQL\\csv-query\\app\\api\\datasets\\route.ts",nextConfigOutput:"",userland:s}),{requestAsyncStorage:l,staticGenerationAsyncStorage:x,serverHooks:m}=d,h="/api/datasets/route";function q(){return(0,o.patchFetch)({serverHooks:m,staticGenerationAsyncStorage:x})}},9487:(e,t,r)=>{"use strict";r.d(t,{a:()=>c,i:()=>s.i6});var s=r(86923),a=r(92048),i=r.n(a),o=r(55315),u=r.n(o);let n=!1;async function c(){if(!n)try{let e=await (0,s.i6)`
      SELECT 1 
      FROM information_schema.tables 
      WHERE table_schema = 'public' AND table_name = 'datasets'
      LIMIT 1;
    `;if(0===e.rowCount){let e=u().join(process.cwd(),"lib","schema.sql"),t=i().readFileSync(e,"utf8");await s.i6.query(t)}n=!0}catch(e){throw console.error("Schema initialization error:",e),Error("Database schema initialization failed.")}}}};var t=require("../../../webpack-runtime.js");t.C(e);var r=e=>t(t.s=e),s=t.X(0,[276,970],()=>r(32017));module.exports=s})();