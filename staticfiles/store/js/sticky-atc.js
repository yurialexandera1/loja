(function () {
  var trigger = document.querySelector('[data-atc-trigger]');
  var bar = document.querySelector('[data-sticky-atc]');
  if (!trigger || !bar || !('IntersectionObserver' in window)) return;

  var mainQty = document.getElementById('qty-input');
  var barQty = bar.querySelector('input[name="qty"]');
  if (mainQty && barQty) {
    barQty.addEventListener('input', function () { mainQty.value = barQty.value; });
    mainQty.addEventListener('input', function () { barQty.value = mainQty.value; });
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      bar.classList.toggle('is-visible', !entry.isIntersecting);
    });
  }, { threshold: 0 });
  observer.observe(trigger);
})();
