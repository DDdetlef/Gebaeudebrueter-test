// Insert a small fixed feedback button (top-left) that opens a mail client
(function(){
  if(document.getElementById('gb-feedback')) return;
  try{
    var a = document.createElement('a');
    a.id = 'gb-feedback';
    a.href = 'mailto:detlefdev@gmail.com?subject=Feedback%20zur%20Karte%20Geb%C3%A4udebr%C3%BCter%20in%20Berlin';
    a.title = 'Feedback senden';
    a.style.position = 'fixed';
    a.style.left = '8px';
    a.style.top = '8px';
    a.style.zIndex = 10010;
    a.style.display = 'inline-block';
    a.style.width = '44px';
    a.style.height = '44px';
    a.style.background = 'transparent';
    a.style.borderRadius = '6px';
    a.style.boxShadow = '0 2px 8px rgba(0,0,0,0.12)';
    a.style.padding = '4px';
    a.style.textDecoration = 'none';
    a.style.cursor = 'pointer';
    var img = document.createElement('img');
    img.src = 'images/edit.png';
    img.alt = 'Feedback';
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.display = 'block';
    img.style.objectFit = 'contain';
    a.appendChild(img);
    // Add some accessible label for screen readers
    var sr = document.createElement('span');
    sr.textContent = 'Feedback senden';
    sr.style.position = 'absolute';
    sr.style.left = '-9999px';
    a.appendChild(sr);
    document.addEventListener('DOMContentLoaded', function(){
      document.body.appendChild(a);
    });
    // If DOM already loaded
    if(document.readyState === 'complete' || document.readyState === 'interactive'){
      if(!document.body) return;
      if(!document.getElementById('gb-feedback')) document.body.appendChild(a);
    }
  }catch(e){console.error('gb_feedback init error', e);}
})();
