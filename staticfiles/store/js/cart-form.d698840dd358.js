(function () {
  document.querySelectorAll('form[action*="update"]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.textContent = 'Atualizando...'; btn.disabled = true; }
    });
  });
  document.querySelectorAll('form[action*="add"]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.textContent = 'Mandando...'; btn.disabled = true; }
    });
  });
})();
