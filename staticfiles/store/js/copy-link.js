(function () {
  var btn = document.querySelector('[data-copy-link]');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var text = btn.getAttribute('data-copy-link');
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(function () {
      if (window.showToast) window.showToast('Link copiado!', 'good');
    });
  });
})();
