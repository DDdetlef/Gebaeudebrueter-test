// Insert a small fixed feedback button (top-left) that opens a mail client
(function(){
  if(document.getElementById('gb-feedback')) return;
  try{
    console.log('gb_feedback: initializing');
    var a = document.createElement('a');
    a.id = 'gb-feedback';
    a.href = 'mailto:detlefdev@gmail.com?subject=Feedback%20zur%20Karte%20Geb%C3%A4udebr%C3%BCter%20in%20Berlin';
    a.title = 'Feedback senden';
    a.setAttribute('aria-label','Feedback senden');
    a.style.position = 'fixed';
    a.style.left = '10px';
    a.style.top = '10px';
    a.style.zIndex = 10050;
    a.style.display = 'inline-block';
    a.style.width = '48px';
    a.style.height = '48px';
    a.style.background = '#ffffff';
    a.style.borderRadius = '8px';
    a.style.boxShadow = '0 3px 10px rgba(0,0,0,0.18)';
    a.style.padding = '6px';
    a.style.textDecoration = 'none';
    a.style.cursor = 'pointer';
    a.style.border = '1px solid rgba(0,0,0,0.08)';
    a.style.transition = 'transform 0.12s ease, box-shadow 0.12s ease';
    a.style.fontSize = '10px';
    a.style.textAlign = 'center';
    a.style.lineHeight = '1.2';
    a.style.color = '#333';
    a.style.fontFamily = 'Arial, sans-serif';
    var img = document.createElement('img');
    img.src = 'images/edit.png';
    img.alt = 'Feedback';
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.display = 'block';
    img.style.objectFit = 'contain';
    img.style.pointerEvents = 'none';
    img.onerror = function(){
      console.log('gb_feedback: image failed, using text fallback');
      a.innerHTML = 'Feedback';
      a.style.fontSize = '10px';
      a.style.paddingTop = '16px';
    };
    a.appendChild(img);
    // Add some accessible label for screen readers
    var sr = document.createElement('span');
    sr.textContent = 'Feedback senden';
    sr.style.position = 'absolute';
    sr.style.left = '-9999px';
    a.appendChild(sr);
    // Hover effects
    a.addEventListener('mouseenter', function(){
      a.style.transform = 'translateY(-2px) scale(1.06)';
      a.style.boxShadow = '0 6px 18px rgba(0,0,0,0.22)';
    });
    a.addEventListener('mouseleave', function(){
      a.style.transform = '';
      a.style.boxShadow = '0 3px 10px rgba(0,0,0,0.18)';
    });
    document.addEventListener('DOMContentLoaded', function(){
      document.body.appendChild(a);
      console.log('gb_feedback: appended to body');
    });
    // If DOM already loaded
    if(document.readyState === 'complete' || document.readyState === 'interactive'){
      if(!document.body) return;
      if(!document.getElementById('gb-feedback')) {
        document.body.appendChild(a);
        console.log('gb_feedback: appended to body (immediate)');
      }
    }
  }catch(e){console.error('gb_feedback init error', e);}
})();
