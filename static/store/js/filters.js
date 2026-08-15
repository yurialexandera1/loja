(function () {
  var toggle = document.querySelector('[data-filters-toggle]');
  var panel = document.getElementById('filters-drawer');
  var backdrop = document.querySelector('[data-filters-backdrop]');
  var closeBtn = document.querySelector('[data-filters-close]');
  if (!toggle || !panel) return;

  function close() {
    panel.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (backdrop) backdrop.hidden = true;
  }
  function open() {
    panel.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');
    if (backdrop) backdrop.hidden = false;
  }
  toggle.addEventListener('click', function () {
    panel.classList.contains('is-open') ? close() : open();
  });
  if (closeBtn) closeBtn.addEventListener('click', close);
  if (backdrop) backdrop.addEventListener('click', close);
  panel.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); toggle.focus(); }
  });
})();
