(function () {
  var header = document.querySelector('.storebar');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  var toggle = document.querySelector('[data-nav-toggle]');
  var panel = document.getElementById('mobile-nav');
  var backdrop = document.querySelector('[data-nav-backdrop]');
  if (!toggle || !panel) return;

  function closeNav() {
    panel.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (backdrop) backdrop.hidden = true;
  }
  function openNav() {
    panel.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');
    if (backdrop) backdrop.hidden = false;
    var firstLink = panel.querySelector('a, button');
    if (firstLink) firstLink.focus();
  }
  toggle.addEventListener('click', function () {
    var isOpen = panel.classList.contains('is-open');
    if (isOpen) closeNav(); else openNav();
  });
  if (backdrop) backdrop.addEventListener('click', closeNav);
  panel.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeNav(); toggle.focus(); }
  });
})();
