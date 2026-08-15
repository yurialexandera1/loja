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

  var navrow = document.querySelector('.navrow');
  if (navrow) {
    var isDown = false, startX, scrollLeft;
    navrow.addEventListener('mousedown', function (e) {
      if (e.target.closest('[data-navmore-toggle]')) return;
      isDown = true;
      startX = e.pageX - navrow.offsetLeft;
      scrollLeft = navrow.scrollLeft;
    });
    window.addEventListener('mouseup', function () { isDown = false; });
    navrow.addEventListener('mouseleave', function () { isDown = false; });
    navrow.addEventListener('mousemove', function (e) {
      if (!isDown) return;
      e.preventDefault();
      var x = e.pageX - navrow.offsetLeft;
      navrow.scrollLeft = scrollLeft - (x - startX);
    });
  }

  var moreToggle = document.querySelector('[data-navmore-toggle]');
  var morePanel = document.querySelector('[data-navmore-panel]');
  if (moreToggle && morePanel) {
    moreToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = !morePanel.hidden;
      morePanel.hidden = isOpen;
      moreToggle.setAttribute('aria-expanded', String(!isOpen));
    });
    document.addEventListener('click', function (e) {
      if (!morePanel.hidden && !e.target.closest('.navmore')) {
        morePanel.hidden = true;
        moreToggle.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !morePanel.hidden) {
        morePanel.hidden = true;
        moreToggle.setAttribute('aria-expanded', 'false');
        moreToggle.focus();
      }
    });
  }
})();
