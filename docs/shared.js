// Shared utilities for Observatorio Económico: Mercado del Huevo en Colombia (UdeA)

window.SHARED = (function () {
  var navLinks = [
    { href: 'index.html', label: 'Observatorio', icon: '&#127968;' },
    { href: 'datos.html', label: 'Concentración & Empresas', icon: '&#128202;' },
    { href: 'ipc.html', label: 'IPC & Macroeconomía', icon: '&#128200;' },
    { href: 'simulacion.html', label: 'Simulación Cournot', icon: '&#9881;' },
    { href: 'citas.html', label: 'Banco de Citas (333)', icon: '&#128221;' },
    { href: 'documentos.html', label: 'Documentos (27)', icon: '&#128214;' },
    { href: 'estado-del-arte.html', label: 'Estado del Arte', icon: '&#128216;' }
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
    var cls = l === 'alta' ? 'badge-green' : l === 'media' ? 'badge-yellow' : 'badge-red';
    return '<span class="badge ' + cls + '">' + l.toUpperCase() + '</span>';
  }

  function qualityBar(dist, total) {
    if (!total || total === 0) return '';
    var colors = { alta: '#10B981', media: '#F59E0B', baja: '#EF4444' };
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
    var page = currentPage();

    var html =
      '<!-- Franja Superior Tricolor Oficial UdeA -->' +
      '<div class="brand-top-bar"></div>' +

      '<!-- Masthead Institucional Superior -->' +
      '<div class="masthead-main">' +
      '  <div class="masthead-container">' +
      '    <a href="index.html" class="masthead-brand-link">' +
      '      <img src="assets/logo_universidad_de_antioquia.svg" class="masthead-shield-img" alt="Escudo Universidad de Antioquia (1803)">' +
      '      <div class="masthead-identity">' +
      '        <div class="masthead-inst-name">UNIVERSIDAD DE ANTIOQUIA</div>' +
      '        <div class="masthead-fac-name">FACULTAD DE CIENCIAS ECONÓMICAS &middot; FERIA DE MICROECONOMÍA II</div>' +
      '        <div class="masthead-site-title">Observatorio Económico: Mercado del Huevo en Colombia</div>' +
      '      </div>' +
      '    </a>' +
      '    <div class="masthead-right">' +
      '      <div class="masthead-badges-row">' +
      '        <span class="badge badge-green">&#10003; SuperSociedades 2015–2025</span>' +
      '        <span class="badge badge-blue">IPC DANE &middot; FENAVI</span>' +
      '      </div>' +
      '      <div class="masthead-btn-row">' +
      '        <button id="theme-toggle-btn" class="theme-toggle" onclick="SHARED.toggleTheme()" title="Cambiar tema (Oscuro / Claro)" aria-label="Cambiar tema"></button>' +
      '        <a href="https://github.com/Ecoudea2025/egg-market-state-of-art" target="_blank" class="btn btn-secondary btn-sm nav-gh-btn" title="Ver repositorio en GitHub">' +
      '          <svg height="15" width="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>' +
      '          <span>GitHub</span>' +
      '        </a>' +
      '        <button class="hamburger" onclick="SHARED.toggleMobileMenu()" aria-label="Menú">&#9776;</button>' +
      '      </div>' +
      '    </div>' +
      '  </div>' +
      '</div>' +

      '<!-- Barra de Navegación Amplia y Centrada -->' +
      '<nav class="masthead-nav">' +
      '  <div class="masthead-nav-container">' +
      '    <ul class="masthead-nav-links">';

    navLinks.forEach(function (link) {
      var active = page === link.href ? ' class="active"' : '';
      html += '<li><a href="' + link.href + '"' + active + '>' + link.icon + ' ' + link.label + '</a></li>';
    });

    html +=
      '    </ul>' +
      '  </div>' +
      '</nav>';

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
      html += '<a href="' + link.href + '"' + active + '>' + link.icon + ' ' + link.label + '</a>';
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
      '<div style="max-width:1200px;margin:0 auto;display:flex;flex-direction:column;align-items:center;gap:14px;">' +
      '<div style="display:flex;align-items:center;gap:16px;">' +
      '<img src="assets/logo_universidad_de_antioquia.svg" alt="UdeA" style="height:48px;">' +
      '<div style="text-align:left;">' +
      '<div style="font-family:\'Times New Roman\',serif;font-size:1.05rem;font-weight:700;letter-spacing:0.06em;color:var(--text-primary);">UNIVERSIDAD DE ANTIOQUIA &middot; 1803</div>' +
      '<div style="font-size:0.8rem;color:var(--udea-green-375);font-weight:600;">Facultad de Ciencias Económicas &middot; Microeconomía II</div>' +
      '</div>' +
      '</div>' +
      '<p class="mt-2" style="font-size:0.82rem;color:var(--text-muted);">' +
      'Observatorio de Investigación del Mercado del Huevo en Colombia &mdash; 15 Empresas (SuperSociedades) &middot; IPC DANE (2015–2025) &middot; FENAVI &middot; 27 Documentos &middot; 333 Citas. ' +
      '<a href="https://github.com/Ecoudea2025/egg-market-state-of-art" target="_blank" style="color:var(--udea-green-361);font-weight:600;">Ver en GitHub</a>' +
      '</p>' +
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
