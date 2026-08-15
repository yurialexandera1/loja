(function () {
  var stage = document.querySelector('[data-gallery-stage]');
  var thumbs = document.querySelectorAll('[data-gallery-thumb]');
  if (!stage || !thumbs.length) return;

  var img = stage.querySelector('img');
  if (!img) return;

  function activate(thumb) {
    var full = thumb.getAttribute('data-full-src');
    var alt = thumb.getAttribute('data-alt') || img.alt;
    if (!full) return;
    img.style.opacity = '0';
    window.setTimeout(function () {
      img.src = full;
      img.alt = alt;
      img.style.opacity = '1';
    }, 120);
    thumbs.forEach(function (t) { t.classList.remove('is-active'); });
    thumb.classList.add('is-active');
  }

  thumbs.forEach(function (thumb, i) {
    thumb.addEventListener('click', function () { activate(thumb); });
    thumb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' && thumbs[i + 1]) { thumbs[i + 1].focus(); activate(thumbs[i + 1]); }
      if (e.key === 'ArrowLeft' && thumbs[i - 1]) { thumbs[i - 1].focus(); activate(thumbs[i - 1]); }
    });
  });
})();
