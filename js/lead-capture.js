/* Sunset Biological Dentistry — lead capture + GoHighLevel submit.
   Auto-attaches to any <form> containing an input[type=email].
   Captures UTM / click-id / offer attribution from the URL (last-touch,
   persisted across pages) and POSTs a JSON body to the GHL inbound webhook,
   then redirects to the confirmation page.

   ONLY edit WEBHOOK below when the client's GHL inbound-webhook URL is ready.
   The payload keys match the GHL merge fields EXACTLY (incl. the space in
   "Full Name") and are identical to the Green Dentistry reference build. */
(function(){
  var WEBHOOK='https://services.leadconnectorhq.com/hooks/OewLxbrWOuUZFrHaXCpZ/webhook-trigger/nlOLbjSwLOGER6N7Wvpn';
  var CONFIRM='/appointment-request-confirmation.html';      // thank-you / conversion page
  // URL query param -> webhook payload key (read in GHL as inboundWebhookRequest.<key>)
  var TRACK={utm_source:'utm_source',utm_medium:'utm_medium',utm_campaign:'utm_campaign',utm_content:'utm_content',gclid:'gclid',fbclid:'fbclid',gbraid:'gbraid',wbraid:'wbraid',offer:'Offer'};
  var KEY='sb_attr';
  function setCookie(n,v,d){var e=new Date();e.setTime(e.getTime()+d*864e5);document.cookie=n+'='+v+';expires='+e.toUTCString()+';path=/;SameSite=Lax';}
  function getCookie(n){var m=document.cookie.match('(?:^|; )'+n+'=([^;]*)');return m?m[1]:'';}
  function readStore(){try{var s=sessionStorage.getItem(KEY);if(s)return JSON.parse(s);}catch(e){}var c=getCookie(KEY);if(c){try{return JSON.parse(decodeURIComponent(c));}catch(e){}}return {};}
  function writeStore(o){var v=JSON.stringify(o);try{sessionStorage.setItem(KEY,v);}catch(e){}setCookie(KEY,encodeURIComponent(v),90);}
  // Capture attribution params on this page (last touch wins) and persist across pages.
  var store=readStore(),params=new URLSearchParams(location.search),changed=false;
  Object.keys(TRACK).forEach(function(p){var val=params.get(p);if(val){store[p]=val;changed=true;}});
  if(changed)writeStore(store);
  function attr(p){return new URLSearchParams(location.search).get(p)||store[p]||'';}
  function val(el){return el&&el.value?el.value.trim():'';}
  function buildPayload(form){
    // Sunset markup: separate first/last name fields (name=fname / name=lname).
    var data={
      'Full Name':(val(form.querySelector('[name=fname]'))+' '+val(form.querySelector('[name=lname]'))).trim(),
      'Email':val(form.querySelector('input[type=email]')),
      'Phone':val(form.querySelector('input[type=tel]'))
    };
    Object.keys(TRACK).forEach(function(p){data[TRACK[p]]=attr(p);});
    return data;
  }
  function done(){location.href=CONFIRM;}
  document.querySelectorAll('form').forEach(function(form){
    if(!form.querySelector('input[type=email]'))return; // only lead-capture forms
    form.setAttribute('novalidate','');
    form.addEventListener('submit',function(ev){
      ev.preventDefault();
      var data=buildPayload(form);
      if(!data['Full Name']||!data.Email||!data.Phone){
        var sel=!data['Full Name']?'[name=fname]':(!data.Email?'input[type=email]':'input[type=tel]');
        var el=form.querySelector(sel);if(el)el.focus();return;
      }
      var btn=form.querySelector('button[type=submit]');
      if(btn){btn.disabled=true;btn.textContent='Sending…';}
      // GHL needs application/json to parse the body; its CORS preflight allows this.
      fetch(WEBHOOK,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),keepalive:true})
        .then(done).catch(done);
    });
  });
})();
