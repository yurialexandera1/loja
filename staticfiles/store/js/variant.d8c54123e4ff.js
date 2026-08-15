(function () {
  var picker = document.querySelector('[data-variant-picker]');
  if (!picker) return;

  var raw = picker.getAttribute('data-variants');
  var variants;
  try { variants = JSON.parse(raw || '[]'); } catch (e) { variants = []; }
  if (!variants.length) return;

  var optionsEl = picker.querySelector('[data-variant-options]');
  var note = picker.querySelector('[data-variant-note]');
  var hiddenInput = document.querySelector('[data-variant-input]');
  var submitBtn = document.querySelector('[data-atc-submit]');
  var qtyInput = document.getElementById('qty-input');
  var mirrorInput = document.querySelector('[data-variant-input-mirror]');
  var mirrorBtn = document.querySelector('[data-atc-submit-mirror]');

  variants.forEach(function (v) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'variant-chip';
    btn.textContent = v.label;
    btn.disabled = v.stock <= 0;
    btn.addEventListener('click', function () { select(v, btn); });
    optionsEl.appendChild(btn);
  });

  function select(variant, btn) {
    optionsEl.querySelectorAll('.variant-chip').forEach(function (b) { b.classList.remove('is-active'); });
    btn.classList.add('is-active');
    if (hiddenInput) hiddenInput.value = variant.id;
    if (mirrorInput) mirrorInput.value = variant.id;
    if (qtyInput) qtyInput.max = variant.stock;
    if (submitBtn) submitBtn.disabled = variant.stock <= 0;
    if (mirrorBtn) mirrorBtn.disabled = variant.stock <= 0;
    if (note) {
      note.textContent = variant.stock > 0
        ? variant.stock + ' em estoque'
        : 'Esgotado nessa variante';
    }
  }
})();
