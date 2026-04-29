/* ============================================================
   Numismatic Collection Manager — JavaScript
   ============================================================ */

'use strict';

// ── Drag-and-drop image upload ─────────────────────────────────────────────
(function initDropZone() {
  const zone = document.getElementById('drop-zone');
  if (!zone) return;

  ['dragenter', 'dragover'].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('drag-over'); })
  );
  ['dragleave', 'drop'].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove('drag-over'); })
  );

  zone.addEventListener('drop', e => {
    const input = document.getElementById('photo-input');
    if (!input) return;
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length) {
      input.files = dt.files;
      // Show filenames
      const label = zone.querySelector('.drop-label span:nth-child(2)');
      if (label) label.textContent = `${dt.files.length} file(s) ready`;
    }
  });

  const input = document.getElementById('photo-input');
  if (input) {
    input.addEventListener('change', () => {
      const label = zone.querySelector('.drop-label span:nth-child(2)');
      if (label && input.files.length)
        label.textContent = `${input.files.length} file(s) selected`;
    });
  }
})();


// ── Auto-dismiss flash messages after 5 s ─────────────────────────────────
(function autoFlash() {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 420);
    }, 5000);
  });
})();


// ── Tag input — show comma-separated preview ──────────────────────────────
(function initTagInput() {
  const input = document.getElementById('tags');
  if (!input) return;

  // Build a small preview row beneath the input
  const preview = document.createElement('div');
  preview.className = 'card-tags';
  preview.style.marginTop = '.35rem';
  input.parentElement.appendChild(preview);

  function render() {
    const tags = input.value.split(',').map(t => t.trim()).filter(Boolean);
    preview.innerHTML = tags.map(t =>
      `<span class="tag">${t}</span>`
    ).join('');
  }

  input.addEventListener('input', render);
  render();
})();


// ── Year-display auto-fill from year_from / year_to ───────────────────────
(function initYearSync() {
  const yFrom = document.getElementById('year_from');
  const yTo   = document.getElementById('year_to');
  const yDisp = document.getElementById('year_display');
  if (!yFrom || !yTo || !yDisp) return;

  function sync() {
    // Only auto-fill if user hasn't written a custom display value
    if (yDisp.dataset.manual === 'true') return;
    const f = yFrom.value.trim();
    const t = yTo.value.trim();
    if (f && t && f !== t) yDisp.value = `${f}–${t}`;
    else if (f) yDisp.value = f;
  }

  yFrom.addEventListener('input', sync);
  yTo.addEventListener('input', sync);
  yDisp.addEventListener('input', () => { yDisp.dataset.manual = 'true'; });
})();


// ── Confirm before dangerous actions (extra safety) ───────────────────────
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    if (!confirm(form.dataset.confirm)) e.preventDefault();
  });
});


// ── Main-photo zoom on click ───────────────────────────────────────────────
(function initPhotoZoom() {
  const photo = document.getElementById('main-photo');
  if (!photo) return;

  photo.addEventListener('click', () => {
    const overlay = document.createElement('div');
    overlay.style.cssText = [
      'position:fixed', 'inset:0', 'z-index:999',
      'background:rgba(0,0,0,.9)', 'display:flex',
      'align-items:center', 'justify-content:center',
      'cursor:zoom-out',
    ].join(';');

    const img = document.createElement('img');
    img.src = photo.src;
    img.style.cssText = 'max-width:92vw;max-height:92vh;object-fit:contain;border-radius:4px;';

    overlay.appendChild(img);
    document.body.appendChild(overlay);
    overlay.addEventListener('click', () => overlay.remove());

    // Keyboard close
    const onKey = e => { if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', onKey); } };
    document.addEventListener('keydown', onKey);
  });
})();


// ── Ruler card bio panel ───────────────────────────────────────────────────
(function initRulerCards() {
  const strip = document.getElementById('rulers-strip');
  const panel = document.getElementById('ruler-bio-panel');
  if (!strip || !panel) return;

  let activeCard = null;

  function renderPanel(card) {
    document.getElementById('rp-name').textContent  = card.dataset.ruler || '';
    document.getElementById('rp-dates').textContent =
      'Reign: ' + (card.dataset.reign || '') +
      '  ·  ' + (card.dataset.born || '') + ' – ' + (card.dataset.died || '');
    document.getElementById('rp-bio').textContent = card.dataset.bio || '';

    const notesEl = document.getElementById('rp-notes');
    const notes   = (card.dataset.notes || '').trim();
    notesEl.style.display = notes ? '' : 'none';
    if (notes) notesEl.textContent = notes;

    panel.style.display = '';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  strip.addEventListener('click', function(e) {
    const card = e.target.closest('.ruler-card');
    if (!card) return;

    // Portrait link navigates to show this ruler's coins
    if (e.target.closest('.ruler-portrait-link')) {
      return;
    }
    // Other links (Edit, coins count) navigate normally
    if (e.target.closest('a')) {
      return;
    }

    if (activeCard === card && panel.style.display !== 'none') {
      panel.style.display = 'none';
      activeCard = null;
      return;
    }
    activeCard = card;
    renderPanel(card);
  });
})();


// ── Export page: keyboard shortcut ────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'a') {
    const selAll = document.querySelector('[onclick="selectAll()"]');
    if (selAll) { e.preventDefault(); selAll.click(); }
  }
});
