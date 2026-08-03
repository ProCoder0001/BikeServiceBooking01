/* ===========================================================
   API base + session helpers, shared by every page.
   Edit API_BASE to point at your running FastAPI backend.
   =========================================================== */
const API_BASE = window.API_BASE || "https://bikeservicebooking.onrender.com";

const Session = {
  setSession(token, user) {
    localStorage.setItem("bsb_token", token);
    localStorage.setItem("bsb_user", JSON.stringify(user));
  },
  getToken() {
    return localStorage.getItem("bsb_token");
  },
  getUser() {
    const raw = localStorage.getItem("bsb_user");
    return raw ? JSON.parse(raw) : null;
  },
  clear() {
    localStorage.removeItem("bsb_token");
    localStorage.removeItem("bsb_user");
  },
  isLoggedIn() {
    return !!this.getToken();
  },
};

async function apiFetch(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && Session.getToken()) {
    headers["Authorization"] = `Bearer ${Session.getToken()}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    /* no body */
  }

  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

async function downloadFile(path, filename) {
  const headers = {};
  if (Session.getToken()) {
    headers["Authorization"] = `Bearer ${Session.getToken()}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      message = data.detail || message;
    } catch (_) {}
    throw new Error(message);
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/* ---------- Nav rendering, shared across pages ---------- */
function renderNav() {
  const slot = document.getElementById("nav-links");
  if (!slot) return;

  const user = Session.getUser();

  if (!user) {
    slot.innerHTML = `
      <a href="/index.html">Home</a>
      <a href="/index.html#services">Services</a>
      <a href="/index.html#contact">Contact</a>
      <a href="/register.html">Register</a>
      <a href="/login.html" class="btn btn-primary btn-sm">Login</a>
    `;
    return;
  }

  if (user.role === "admin") {
    slot.innerHTML = `
      <a href="/admin/all-bikes.html">Bikes</a>
      <a href="/admin/all-customers.html">Customers</a>
      <a href="/admin/all-bookings.html">Bookings</a>
      <span class="muted mono" style="font-size:.8rem">${user.first_name}</span>
      <a href="#" id="logout-link" class="btn btn-outline btn-sm">Logout</a>
    `;
  } else {
    slot.innerHTML = `
      <a href="/customer/wallet.html">Wallet</a>
      <a href="/customer/add-bike.html">Add Bike</a>
      <a href="/customer/my-bikes.html">My Bikes</a>
      <a href="/customer/book-service.html">Book Service</a>
      <a href="/customer/my-bookings.html">My Bookings</a>
      <a href="#" id="logout-link" class="btn btn-outline btn-sm">Logout</a>
    `;
  }

  const logout = document.getElementById("logout-link");
  if (logout) {
    logout.addEventListener("click", (e) => {
      e.preventDefault();
      Session.clear();
      window.location.href = "/index.html";
    });
  }
}

/* Redirect guard for protected pages. Call at top of page script. */
function requireRole(role) {
  const user = Session.getUser();
  if (!user || !Session.getToken()) {
    window.location.href = "/login.html";
    return null;
  }
  if (user.role !== role) {
    window.location.href = user.role === "admin" ? "/admin/all-bookings.html" : "/customer/my-bookings.html";
    return null;
  }
  return user;
}

function showAlert(el, message, type = "error") {
  if (!el) return;
  el.textContent = message;
  el.className = `alert show alert-${type}`;
}

function badgeClass(status) {
  const s = (status || "").toLowerCase();
  if (s === "pending") return "badge-pending";
  if (s === "approved" || s === "completed") return "badge-approved";
  if (s === "cancelled") return "badge-cancelled";
  return "badge-pending";
}

function fmtMoney(n) {
  return `Rs ${Number(n || 0).toFixed(2)}`;
}

document.addEventListener("DOMContentLoaded", renderNav);
