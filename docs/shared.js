// Shared utilities for the egg-market-state-of-art documentation site
// Supports responsive mobile navigation with hamburger menu

window.SHARED = (function() {

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

  // --- Quality badge ---
  function qualityBadge(level) {
    var cls = level === 'alta' ? 'badge-green' : level === 'media' ? 'badge-yellow' : 'badge-orange';
    return '<span class="badge ' + cls + '">' + level.toUpperCase() + '</span>';
  }

  // --- Quality bar ---
  function qualityBar(dist, total) {
    if (!total || total === 0) return '';
    var colors = { alta: '#22c55e', media: '#eab308', baja: '#f97316' };
    var html = '';
    ['alta', 'media', 'baja'].forEach(function(q) {
      var count = dist[q] || 0;
      var pct = Math.round((count / total) * 100);
      html += '<div class="quality-bar">' +
        '<span class="bar-label" style="color:' + colors[q] + '">' + q.toUpperCase() + '</span>' +
        '<div class="bar-track"><div class="bar-fill" style="width:' + pct + '%;background:' + colors[q] + '"></div></div>' +
        '<span class="bar-count">' + count + '</span>' +
      '</div>';
    });
    return html;
  }

  // --- Topic tags ---
  function topicTags(topics) {
    if (!topics || !topics.length) return '';
    return topics.map(function(t) { return '<span class="badge badge-gray">' + esc(t) + '</span>'; }).join(' ');
  }

  // --- Get current page ---
  function currentPage() {
    var path = window.location.pathname;
    var page = path.split('/').pop() || 'index.html';
    if (page === '' || page === '/') page = 'index.html';
    return page;
  }

  // --- Nav links config ---
  var navLinks = [
    { href: 'index.html', label: 'Inicio' },
    { href: 'citas.html', label: 'Citas' },
    { href: 'documentos.html', label: 'Documentos' },
    { href: 'estado-del-arte.html', label: 'Estado del Arte' },
  ];

  // --- Render navbar (desktop) ---
  function renderNav() {
    var nav = document.getElementById('navbar');
    if (!nav) return;
    var page = currentPage();

    var html = '<a href="index.html" class="navbar-brand"><span>&#9670;</span> Estado del Arte: Mercado del Huevo</a>';

    // Desktop links
    html += '<ul class="navbar-links">';
    navLinks.forEach(function(link) {
      var active = (page === link.href) ? ' class="active"' : '';
      html += '<li><a href="' + link.href + '"' + active + '>' + link.label + '</a></li>';
    });
    html += '</ul>';

    // Hamburger button (mobile)
    html += '<button class="hamburger" onclick="SHARED.toggleMobileMenu()" aria-label="Menu">&#9776;</button>';

    nav.innerHTML = html;
  }

  // --- Mobile menu overlay + panel ---
  function renderMobileMenu() {
    var body = document.body;

    // Overlay
    var overlay = document.createElement('div');
    overlay.className = 'mobile-nav-overlay';
    overlay.id = 'mobile-overlay';
    overlay.onclick = function() { toggleMobileMenu(); };
    body.appendChild(overlay);

    // Menu panel
    var menu = document.createElement('div');
    menu.className = 'mobile-nav-menu';
    menu.id = 'mobile-menu';
    var page = currentPage();

    var html = '<button class="close-btn" onclick="SHARED.toggleMobileMenu()" aria-label="Cerrar">&times;</button>';
    navLinks.forEach(function(link) {
      var active = (page === link.href) ? ' class="active"' : '';
      html += '<a href="' + link.href + '"' + active + '>' + link.label + '</a>';
    });
    menu.innerHTML = html;
    body.appendChild(menu);
  }

  // --- Toggle mobile menu ---
  window.toggleMobileMenu = function() {
    var overlay = document.getElementById('mobile-overlay');
    var menu = document.getElementById('mobile-menu');
    if (!overlay || !menu) return;

    var isOpen = menu.classList.contains('open');
    if (isOpen) {
      overlay.classList.remove('open');
      menu.classList.remove('open');
    } else {
      overlay.classList.add('open');
      menu.classList.add('open');
    }
  };

  window.SHARED.toggleMobileMenu = window.toggleMobileMenu;

  // --- Render footer ---
  function renderFooter() {
    var footer = document.getElementById('footer');
    if (!footer) return;
    footer.innerHTML =
      '<p>Proyecto de investigacion en microeconomia aplicada &mdash; Mercado del Huevo en Colombia</p>' +
      '<p class="mt-2">Basado en 27 documentos academicos procesados con extraccion automatica de citas y filtrado semantico. ' +
      '<a href="https://github.com/Ecoudea2025/egg-market-state-of-art" target="_blank">Ver en GitHub</a></p>';
  }

  // --- Initialize ---
  function init() {
    document.addEventListener('DOMContentLoaded', function() {
      renderNav();
      renderMobileMenu();
      renderFooter();
    });
  }

  return {
    esc: esc,
    truncate: truncate,
    qualityBadge: qualityBadge,
    qualityBar: qualityBar,
    topicTags: topicTags,
    renderNav: renderNav,
    renderFooter: renderFooter,
    init: init,
    currentPage: currentPage,
    toggleMobileMenu: window.toggleMobileMenu,
  };
})();

SHARED.init();
