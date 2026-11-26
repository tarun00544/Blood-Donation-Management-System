/**
 * BLOODCARE - Portal Application Framework
 * Automatically initializes User or Admin layout, sidebar navigation, topbar,
 * mobile drawer, notification popovers, and page state.
 */

const USER_NAV = [
  { href: '/user/dashboard.html', label: 'Dashboard', icon: '📊' },
  { href: '/user/profile.html', label: 'My Profile', icon: '👤' },
  { href: '/user/become-donor.html', label: 'Become a Donor', icon: '❤️' },
  { href: '/user/find-donors.html', label: 'Find Donors', icon: '🔍' },
  { href: '/user/blood-availability.html', label: 'Blood Availability', icon: '🩸' },
  { href: '/user/request-blood.html', label: 'Request Blood', icon: '➕' },
  { href: '/user/my-requests.html', label: 'My Requests', icon: '📋' }
];

const ADMIN_NAV = [
  { href: '/admin/dashboard.html', label: 'Dashboard', icon: '📈' },
  { href: '/admin/donors.html', label: 'Donor Management', icon: '❤️' },
  { href: '/admin/hospitals.html', label: 'Hospitals', icon: '🏥' },
  { href: '/admin/recipients.html', label: 'Recipients', icon: '👥' },
  { href: '/admin/inventory.html', label: 'Blood Inventory', icon: '🩸' },
  { href: '/admin/requests.html', label: 'Blood Requests', icon: '📋' },
  { href: '/admin/reports.html', label: 'Reports & Analytics', icon: '📊' },
  { href: '/admin/users.html', label: 'User Management', icon: '🛡️' }
];

async function initializePortal() {
  const portal = document.body.dataset.portal; // 'user' or 'admin'
  if (!portal) return; // Landing page or auth pages don't need sidebar layout

  // Enforce server-side role check
  let currentUser;
  if (portal === 'admin') {
    currentUser = await auth.requireAdmin();
  } else {
    currentUser = await auth.requireUser();
  }
  if (!currentUser) return; // Redirection handled in auth.js

  const currentPath = window.location.pathname;
  const navItems = portal === 'admin' ? ADMIN_NAV : USER_NAV;
  const portalLabel = portal === 'admin' ? 'Admin Portal' : 'User Portal';
  const pageTitle = document.body.dataset.pageTitle || 'Dashboard';

  // Build navigation HTML
  const navHtml = navItems.map(item => {
    const isActive = currentPath.endsWith(item.href) || (item.href.includes('dashboard') && (currentPath.endsWith('/user/') || currentPath.endsWith('/admin/')));
    return `
      <li>
        <a href="${item.href}" class="${isActive ? 'active' : ''}">
          <span class="menu-icon">${item.icon}</span>
          <span>${item.label}</span>
        </a>
      </li>
    `;
  }).join('');

  // Find target main container
  const pageContent = document.getElementById('pageContent') || document.getElementById('content');
  if (!pageContent) return;

  const appContainer = document.createElement('div');
  appContainer.className = 'app-container';
  appContainer.innerHTML = `
    <!-- Mobile Overlay -->
    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <!-- Sidebar Navigation -->
    <aside class="app-sidebar" id="appSidebar">
      <div class="sidebar-brand">
        <span class="brand-icon">🩸</span>
        <div style="flex:1">
          <div class="brand-text">BLOODCARE</div>
          <span class="brand-badge">${portalLabel}</span>
        </div>
      </div>

      <ul class="sidebar-menu">
        ${navHtml}
      </ul>

      <div class="sidebar-footer">
        <div class="user-snippet">
          <div class="user-avatar">${esc(currentUser.name.charAt(0).toUpperCase())}</div>
          <div class="user-info">
            <div class="user-name">${esc(currentUser.name)}</div>
            <div class="user-role">${esc(currentUser.role)}</div>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" style="width:100%; justify-content:center;" id="logoutBtn">
          🚪 Logout
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="app-main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="mobile-toggle" id="mobileToggle" aria-label="Toggle menu">☰</button>
          <h1 class="topbar-title">${esc(pageTitle)}</h1>
        </div>
        <div class="topbar-right">
          <button class="btn btn-outline btn-sm" id="notificationsBtn" title="Notifications">
            🔔 <span id="notifBadge" style="display:none; color:var(--primary); font-weight:bold;">•</span>
          </button>
          <a href="${portal === 'admin' ? '/admin/dashboard.html' : '/user/dashboard.html'}" class="btn btn-outline btn-sm">
            🏠 Portal Home
          </a>
        </div>
      </header>
      <main class="page-shell" id="appShell"></main>
    </div>
  `;

  // Insert before content and move content inside shell
  document.body.prepend(appContainer);
  document.getElementById('appShell').appendChild(pageContent);

  // Setup Sidebar Toggle for Mobile
  const sidebar = document.getElementById('appSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('mobileToggle');

  const toggleSidebar = () => {
    sidebar.classList.toggle('sidebar-open');
    overlay.classList.toggle('active');
  };

  if (toggleBtn) toggleBtn.onclick = toggleSidebar;
  if (overlay) overlay.onclick = toggleSidebar;

  // Setup Logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.onclick = () => auth.logout();
  }

  // Setup Notifications
  const notifBtn = document.getElementById('notificationsBtn');
  if (notifBtn) {
    notifBtn.onclick = async () => {
      if (portal === 'user') {
        try {
          const res = await api.get('/user/notifications');
          const notifs = res.data || [];
          if (!notifs.length) {
            openModal('Notifications', '<div class="state-box">No new notifications at this time.</div>');
            return;
          }
          const html = `
            <div style="display:flex; flex-direction:column; gap:12px;">
              ${notifs.map(n => `
                <div class="alert-banner alert-${n.type === 'error' ? 'danger' : n.type === 'info' ? 'info' : n.type === 'warning' ? 'warning' : 'info'}" style="margin:0;">
                  <span class="alert-icon">${n.type === 'success' ? '✓' : n.type === 'warning' ? '⚠' : 'ℹ'}</span>
                  <div class="alert-content">
                    <div style="font-weight:700; margin-bottom:2px;">${esc(n.title)}</div>
                    <div>${esc(n.message)}</div>
                    ${n.date ? `<div style="font-size:11px; opacity:0.8; margin-top:4px;">${fmtDateTime(n.date)}</div>` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          `;
          openModal('My Notifications', html);
        } catch (e) {
          toast(e.message, 'error');
        }
      } else {
        // Admin Notifications: Check low stock
        try {
          const d = await api.get('/dashboard');
          const data = d.data || {};
          const low = data.low_stock_blood_groups || [];
          const pending = data.pending_requests || 0;
          let html = '<div style="display:flex; flex-direction:column; gap:12px;">';
          if (pending > 0) {
            html += `
              <div class="alert-banner alert-warning" style="margin:0;">
                <span class="alert-icon">📋</span>
                <div class="alert-content">
                  <b>${pending} Pending Blood Request(s)</b>
                  <div>There are blood requests waiting for approval.</div>
                  <div style="margin-top:6px;"><a href="/admin/requests.html" class="btn btn-sm btn-primary">Review Requests</a></div>
                </div>
              </div>
            `;
          }
          if (low.length > 0) {
            html += `
              <div class="alert-banner alert-danger" style="margin:0;">
                <span class="alert-icon">⚠</span>
                <div class="alert-content">
                  <b>Critical Low Stock Alert</b>
                  <div>The following blood groups have fewer than ${data.low_stock_threshold || 10} units:</div>
                  <div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap;">
                    ${low.map(x => `<span class="badge badge-danger">${esc(x.blood_group)}: ${x.units_available} units</span>`).join('')}
                  </div>
                </div>
              </div>
            `;
          }
          if (pending === 0 && low.length === 0) {
            html += '<div class="state-box">All blood stocks and requests are currently normal.</div>';
          }
          html += '</div>';
          openModal('System Alerts & Notifications', html);
        } catch (e) {
          toast(e.message, 'error');
        }
      }
    };
  }
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', initializePortal);
