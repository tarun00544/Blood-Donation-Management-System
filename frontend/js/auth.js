/**
 * BLOODCARE - Authentication and Layout Helper
 * Manages user session state, role validation, alerts, and navigation.
 */

const auth = {
  currentUser: null,

  async checkSession() {
    try {
      const res = await api.get('/auth/me', { silentAuth: true });
      if (res && res.success && res.data) {
        this.currentUser = res.data;
        return this.currentUser;
      }
    } catch (e) {
      this.currentUser = null;
    }
    return null;
  },

  async requireUser(redirectPath = '/user-login.html') {
    const user = await this.checkSession();
    if (!user) {
      toast('Please log in to access this page', 'warn');
      setTimeout(() => {
        window.location.href = redirectPath;
      }, 500);
      return null;
    }
    return user;
  },

  async requireAdmin(redirectPath = '/admin-login.html') {
    const user = await this.checkSession();
    if (!user) {
      toast('Please log in as an administrator', 'warn');
      setTimeout(() => {
        window.location.href = redirectPath;
      }, 500);
      return null;
    }
    if (user.role !== 'admin') {
      toast('Access denied. Administrator privileges required.', 'error');
      setTimeout(() => {
        window.location.href = '/user/dashboard.html';
      }, 1000);
      return null;
    }
    return user;
  },

  async logout() {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.warn('Logout error:', e);
    }
    this.currentUser = null;
    toast('Logged out successfully', 'info');
    setTimeout(() => {
      window.location.href = '/index.html';
    }, 400);
  }
};

// UI Helpers
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

const fmtDate = (d) => {
  if (!d) return '—';
  try {
    const date = new Date(d);
    if (isNaN(date.getTime())) return d;
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch (e) {
    return d;
  }
};

const fmtDateTime = (d) => {
  if (!d) return '—';
  try {
    const date = new Date(d);
    if (isNaN(date.getTime())) return d;
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return d;
  }
};

const badge = (text, type = 'default') => {
  const clsMap = {
    'red': 'badge-red',
    'Pending': 'badge-warning',
    'Approved': 'badge-info',
    'Fulfilled': 'badge-success',
    'Rejected': 'badge-danger',
    'Available': 'badge-success',
    'Unavailable': 'badge-secondary',
    'Valid': 'badge-success',
    'Expiring Soon': 'badge-warning',
    'Expired': 'badge-danger',
    'admin': 'badge-danger',
    'user': 'badge-info'
  };
  const cls = clsMap[type] || clsMap[text] || 'badge-default';
  return `<span class="badge ${cls}">${esc(text)}</span>`;
};

function toast(msg, type = 'success') {
  let box = document.getElementById('toastContainer');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toastContainer';
    box.className = 'toast-container';
    document.body.appendChild(box);
  }
  const t = document.createElement('div');
  t.className = `toast-item toast-${type}`;
  
  const icon = type === 'error' ? '✕' : type === 'warn' ? '⚠' : type === 'info' ? 'ℹ' : '✓';
  t.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-text">${esc(msg)}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
  box.appendChild(t);
  setTimeout(() => {
    t.classList.add('toast-fade');
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

function openModal(title, htmlContent, maxWidth = '560px') {
  const existing = document.querySelector('.modal-backdrop');
  if (existing) existing.remove();

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
    <div class="modal-dialog" style="max-width: ${maxWidth}">
      <div class="modal-header">
        <h3 class="modal-title">${esc(title)}</h3>
        <button class="modal-close" data-close>&times;</button>
      </div>
      <div class="modal-body">${htmlContent}</div>
    </div>
  `;
  backdrop.onclick = (e) => {
    if (e.target === backdrop || e.target.hasAttribute('data-close') || e.target.closest('[data-close]')) {
      backdrop.remove();
    }
  };
  document.body.appendChild(backdrop);
  return backdrop;
}

function initPasswordToggle(inputSelector, toggleButtonSelector) {
  const inputs = document.querySelectorAll(inputSelector);
  inputs.forEach((input) => {
    const parent = input.parentElement;
    let btn = parent.querySelector(toggleButtonSelector);
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pwd-toggle-btn';
      btn.title = 'Show/hide password';
      btn.innerHTML = '👁';
      parent.style.position = 'relative';
      parent.appendChild(btn);
    }
    btn.onclick = () => {
      if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '🙈';
      } else {
        input.type = 'password';
        btn.innerHTML = '👁';
      }
    };
  });
}

window.auth = auth;
window.toast = toast;
window.openModal = openModal;
window.badge = badge;
window.esc = esc;
window.fmtDate = fmtDate;
window.fmtDateTime = fmtDateTime;
window.initPasswordToggle = initPasswordToggle;
