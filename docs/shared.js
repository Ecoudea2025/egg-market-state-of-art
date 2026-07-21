// Shared utilities for the egg-market-state-of-art documentation site
// Called by: index.html, citas.html, documentos.html, estado-del-arte.html

window.SHARED = (function() {

  // --- Data loading ---
  function loadData(key, callback) {
    if (window[key] && window[key].length > 0) {
      callback(window[key]);
      return;
    }
    const varLower = key.toLowerCase().replace('_data', '');
    fetch(`data/${varLower}.json`)
      .then(r => r.json())
      .then(d => { window[key] = d; callback(d); })
      .catch(() => console.warn(`Could not load ${key} from JSON, trying JS`));
  }

  // --- Navigation ---
  function highlightNav() {
    const path = window.location.pathname;
    const page = path.split('/').pop() || 'index.html';
    document.querySelectorAll('.navbar-links a').forEach(a => {
      const href = a.getAttribute('href');
      if (href === page || (page === '' && href === 'index.html')) {
        a.classList.add('active');
      }
    });
  }

  // --- Escape HTML ---
  function esc(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;')
              .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // --- Truncate text ---
  function truncate(str, max) {
    if (!str) return '';
    if (str.length <= max) return str;
    return str.substring(0, max) + '...';
  }

  // --- Quality badge HTML ---
  function qualityBadge(level) {
    const cls = level === 'alta' ? 'badge-green' : level === 'media' ? 'badge-yellow' : 'badge-orange';
    return `<span class="badge ${cls}">${level.toUpperCase()}</span>`;
  }

  // --- Quality bar HTML ---
  function qualityBar(dist, total) {
    if (!total || total === 0) return '';
    const colors = { alta: '#22c55e', media: '#eab308', baja: '#f97316' };
    let html = '';
    ['alta', 'media', 'baja'].forEach(q => {
      const count = dist[q] || 0;
      const pct = Math.round((count / total) * 100);
      html += `<div class="quality-bar">
        <span class="bar-label" style="color:${colors[q]}">${q.toUpperCase()}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${colors[q]}"></div></div>
        <span class="bar-count">${count}</span>
      </div>`;
    });
    return html;
  }

  // --- Topic tags ---
  function topicTags(topics) {
    if (!topics || !topics.length) return '';
    return topics.map(t => `<span class="badge badge-gray">${esc(t)}</span>`).join(' ');
  }

  // --- Render navigation bar ---
  function renderNav() {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    nav.innerHTML = `
      <a href="index.html" class="navbar-brand">
        <span>&#9670;</span> Estado del Arte: Mercado del Huevo
      </a>
      <ul class="navbar-links">
        <li><a href="index.html">Inicio</a></li>
        <li><a href="citas.html">Citas</a></li>
        <li><a href="documentos.html">Documentos</a></li>
        <li><a href="estado-del-arte.html">Estado del Arte</a></li>
      </ul>`;
    highlightNav();
  }

  // --- Render footer ---
  function renderFooter() {
    const footer = document.getElementById('footer');
    if (!footer) return;
    footer.innerHTML = `
      <p>Proyecto de investigacion en microeconomia aplicada — Mercado del Huevo en Colombia</p>
      <p class="mt-2">Basado en 27 documentos academicos procesados con extraccion automatica de citas y filtrado semantico.</p>`;
  }

  // --- Initialize page ---
  function init() {
    document.addEventListener('DOMContentLoaded', () => {
      renderNav();
      renderFooter();
    });
  }

  return {
    loadData,
    esc,
    truncate,
    qualityBadge,
    qualityBar,
    topicTags,
    renderNav,
    renderFooter,
    init,
  };
})();

SHARED.init();
