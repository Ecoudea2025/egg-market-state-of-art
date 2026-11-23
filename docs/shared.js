// Shared utilities for Observatorio Económico: Mercado del Huevo en Colombia (UdeA)

window.SHARED = (function () {
  var navLinks = [
    { href: 'index.html', label: 'Observatorio' },
    { href: 'datos.html', label: 'Concentración & Empresas' },
    { href: 'ipc.html', label: 'IPC & Macroeconomía' },
    { href: 'simulacion.html', label: 'Simulación Cournot' },
    { href: 'citas.html', label: 'Banco de Citas' },
    { href: 'documentos.html', label: 'Documentos' },
    { href: 'estado-del-arte.html', label: 'Estado del Arte' }
  ];

  function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function truncate(str, max) {
    if (!str) return '';
    if (str.length <= max) return str;
    return str.substring(0, max) + '...';
  }

  function formatNumber(val, decimals) {
    if (val === null || val === undefined || isNaN(val)) return '—';
    var d = decimals !== undefined ? decimals : 0;
    return Number(val).toLocaleString('es-CO', {
      minimumFractionDigits: d,
      maximumFractionDigits: d
    });
  }

  function formatCOP(val, inMillions) {
    if (val === null || val === undefined || isNaN(val)) return '—';
    if (inMillions) {
      return '$ ' + formatNumber(val / 1e6, 1) + ' M';
    }
    return '$ ' + formatNumber(val, 0);
  }

  function formatPct(val, decimals) {
    if (val === null || val === undefined || isNaN(val)) return '—';
    var d = decimals !== undefined ? decimals : 2;
    return Number(val).toFixed(d) + '%';
  }

  function qualityBadge(level) {
    var l = (level || 'media').toLowerCase();
    var cls = l === 'alta' ? 'badge-green' : l === 'media' ? 'badge-yellow' : 'badge-orange';
    return '<span class="badge ' + cls + '">' + l.toUpperCase() + '</span>';
  }

  function qualityBar(dist, total) {
    if (!total || total === 0) return '';
    var colors = { alta: '#43B649', media: '#F9A12C', baja: '#EF434D' };
    var html = '';
    ['alta', 'media', 'baja'].forEach(function (q) {
      var count = dist[q] || 0;
      var pct = Math.round((count / total) * 100);
      html +=
        '<div class="quality-bar">' +
        '<span class="bar-label" style="color:' + colors[q] + '">' + q.toUpperCase() + '</span>' +
        '<div class="bar-track"><div class="bar-fill" style="width:' + pct + '%;background:' + colors[q] + '"></div></div>' +
        '<span class="bar-count">' + count + '</span>' +
        '</div>';
    });
    return html;
  }

  function topicTags(topics) {
    if (!topics || !topics.length) return '';
    return topics.map(function (t) { return '<span class="badge badge-gray">' + esc(t) + '</span>'; }).join(' ');
  }

  function currentPage() {
    var path = window.location.pathname;
    var page = path.split('/').pop() || 'index.html';
    if (page === '' || page === '/') page = 'index.html';
    return page;
  }

  function getTheme() {
    return localStorage.getItem('udea_egg_theme') || 'dark';
  }

  function applyTheme(theme) {
    var isLight = theme === 'light';
    if (isLight) {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    var btn = document.getElementById('theme-toggle-btn');
    if (btn) btn.innerHTML = isLight ? '&#9790;' : '&#9728;';

    // Actualizar logo según el tema
    var logo = document.getElementById('navbar-logo-img');
    if (logo) {
      logo.src = isLight ? 'assets/logo-udea-simplificado.svg' : 'assets/logo-udea-simplificado-blanco.svg';
    }
  }

  function toggleTheme() {
    var next = getTheme() === 'dark' ? 'light' : 'dark';
    localStorage.setItem('udea_egg_theme', next);
    applyTheme(next);
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: next } }));
  }

  function plotlyLayout(custom) {
    var isLight = getTheme() === 'light';
    var textColor = isLight ? '#284435' : '#a3c4b2';
    var gridColor = isLight ? 'rgba(2, 105, 55, 0.08)' : 'rgba(67, 182, 73, 0.12)';
    var base = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'Inter, sans-serif', color: textColor, size: 12 },
      margin: { t: 36, r: 24, b: 48, l: 58 },
      xaxis: { gridcolor: gridColor, zerolinecolor: gridColor },
      yaxis: { gridcolor: gridColor, zerolinecolor: gridColor },
      legend: { orientation: 'h', y: -0.22, font: { color: textColor } },
      hoverlabel: {
        bgcolor: isLight ? '#ffffff' : '#0d1a13',
        bordercolor: isLight ? '#b0d4bf' : '#35944B',
        font: { color: isLight ? '#0a1c12' : '#f4fbf7', family: 'Inter, sans-serif' }
      }
    };
    return Object.assign({}, base, custom || {});
  }

  function downloadCSV(filename, headers, rows) {
    var lines = [headers.join(',')];
    rows.forEach(function (r) {
      var line = r.map(function (cell) {
        var s = cell === null || cell === undefined ? '' : String(cell);
        return '"' + s.replace(/"/g, '""') + '"';
      }).join(',');
      lines.push(line);
    });
    var blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function renderNav() {
    var nav = document.getElementById('navbar');
    if (!nav) return;

    var isLight = getTheme() === 'light';
    var logoSrc = isLight ? 'assets/logo-udea-simplificado.svg' : 'assets/logo-udea-simplificado-blanco.svg';
    var page = currentPage();

    var html =
      '<div class="brand-top-bar" style="position:absolute;top:0;left:0;right:0;"></div>' +
      '<a href="index.html" class="navbar-brand">' +
      '<img id="navbar-logo-img" class="navbar-logo-img" src="' + logoSrc + '" alt="Universidad de Antioquia Logo">' +
      '<div class="navbar-brand-texts">' +
      '<span class="navbar-brand-title">Observatorio Huevo UdeA</span>' +
      '<span class="navbar-brand-sub">Microeconomía II &middot; Ciencias Económicas</span>' +
      '</div>' +
      '</a>';

    html += '<ul class="navbar-links">';
    navLinks.forEach(function (link) {
      var active = page === link.href ? ' class="active"' : '';
      html += '<li><a href="' + link.href + '"' + active + '>' + link.label + '</a></li>';
    });
    html += '</ul>';

    html +=
      '<div class="nav-actions">' +
      '<button id="theme-toggle-btn" class="theme-toggle" onclick="SHARED.toggleTheme()" title="Cambiar tema" aria-label="Cambiar tema"></button>' +
      '<button class="hamburger" onclick="SHARED.toggleMobileMenu()" aria-label="Menú">&#9776;</button>' +
      '</div>';

    nav.innerHTML = html;
    applyTheme(getTheme());
  }

  function renderMobileMenu() {
    var body = document.body;
    var overlay = document.createElement('div');
    overlay.className = 'mobile-nav-overlay';
    overlay.id = 'mobile-overlay';
    overlay.onclick = toggleMobileMenu;
    body.appendChild(overlay);

    var menu = document.createElement('div');
    menu.className = 'mobile-nav-menu';
    menu.id = 'mobile-menu';
    var page = currentPage();

    var html = '<button class="close-btn" onclick="SHARED.toggleMobileMenu()" aria-label="Cerrar">&times;</button>';
    navLinks.forEach(function (link) {
      var active = page === link.href ? ' class="active"' : '';
      html += '<a href="' + link.href + '"' + active + '>' + link.label + '</a>';
    });
    menu.innerHTML = html;
    body.appendChild(menu);
  }

  function toggleMobileMenu() {
    var overlay = document.getElementById('mobile-overlay');
    var menu = document.getElementById('mobile-menu');
    if (!overlay || !menu) return;
    overlay.classList.toggle('open');
    menu.classList.toggle('open');
  }

  function renderFooter() {
    var footer = document.getElementById('footer');
    if (!footer) return;
    footer.innerHTML =
      '<div style="max-width:1200px;margin:0 auto;display:flex;flex-direction:column;align-items:center;gap:12px;">' +
      '<div style="display:flex;align-items:center;gap:12px;">' +
      '<img src="assets/logo-udea-simplificado-blanco.svg" alt="UdeA" style="height:32px;opacity:0.9;">' +
      '<div style="text-align:left;">' +
      '<div style="font-weight:700;color:var(--text-primary);letter-spacing:-0.01em;">Universidad de Antioquia &middot; Facultad de Ciencias Económicas</div>' +
      '<div style="font-size:0.75rem;color:var(--text-muted);">Investigación de Mercados y Estructuras Oligopólicas en Colombia</div>' +
      '</div>' +
      '</div>' +
      '<p class="mt-2">Fuentes: SuperSociedades (15 empresas, 2015–2025) &middot; DANE (IPC 2015–2025) &middot; FENAVI &middot; 27 Documentos Académicos &middot; 333 Citas. ' +
      '<a href="https://github.com/Ecoudea2025/egg-market-state-of-art" target="_blank">Ver en GitHub</a></p>' +
      '</div>';
  }

  function init() {
    applyTheme(getTheme());
    document.addEventListener('DOMContentLoaded', function () {
      renderNav();
      renderMobileMenu();
      renderFooter();
    });
  }

  return {
    esc: esc,
    truncate: truncate,
    formatNumber: formatNumber,
    formatCOP: formatCOP,
    formatPct: formatPct,
    qualityBadge: qualityBadge,
    qualityBar: qualityBar,
    topicTags: topicTags,
    renderNav: renderNav,
    renderFooter: renderFooter,
    init: init,
    currentPage: currentPage,
    toggleMobileMenu: toggleMobileMenu,
    toggleTheme: toggleTheme,
    getTheme: getTheme,
    plotlyLayout: plotlyLayout,
    downloadCSV: downloadCSV
  };
})();

SHARED.init();
