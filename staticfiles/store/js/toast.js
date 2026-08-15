(function () {
  var container = document.getElementById('toast-container');
  if (!container) return;
  var timers = {};
  window.showToast = function (message, type) {
    type = type || 'info';
    var existing = container.querySelector('.toast-' + type);
    if (existing) {
      existing.textContent = message;
      existing.classList.remove('toast-hidden');
      clearTimeout(timers[type]);
    } else {
      var el = document.createElement('div');
      el.className = 'toast toast-' + type;
      el.textContent = message;
      container.appendChild(el);
    }
    timers[type] = setTimeout(function () {
      var e = container.querySelector('.toast-' + type);
      if (e) e.classList.add('toast-hidden');
    }, 3000);
  };
})();
