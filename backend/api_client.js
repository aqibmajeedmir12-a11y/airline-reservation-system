/* ═══════════════════════════════════════════════════════
   SkyFlow API Client  — Flask Backend Connector
   All calls go to /api/* on the same server
   Handles authentication + token automatically
   ═══════════════════════════════════════════════════════ */

window.API = (function() {
  function getToken() {
    return sessionStorage.getItem('sf_token') || '';
  }
  function setToken(t) {
    sessionStorage.setItem('sf_token', t);
  }
  function getUser() {
    try {
      return JSON.parse(sessionStorage.getItem('sf_user'));
    } catch (e) {
      return null;
    }
  }
  function setUser(u) {
    sessionStorage.setItem('sf_user', JSON.stringify(u));
  }
  function clearAuth() {
    sessionStorage.removeItem('sf_token');
    sessionStorage.removeItem('sf_user');
  }

  // Unwrap { success, data: {...} } OR pass through flat responses
  function unwrap(json) {
    if (json && typeof json === 'object' && 'success' in json && 'data' in json) {
      return json.data;
    }
    return json;
  }

  async function req(path, opts) {
    opts = opts || {};
    var base = window.location.origin + '/api';
    var headers = { 'Content-Type': 'application/json' };
    var token = getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;
    var res = await fetch(base + path, {
      method: opts.method || 'GET',
      headers: headers,
      body: opts.body || undefined
    });
    var json = await res.json().catch(function() {
      return {};
    });
    if (!res.ok) {
      var msg = json.error || json.message || ('Request failed (' + res.status + ')');
      throw new Error(msg);
    }
    return unwrap(json);
  }

  return {
    getToken: getToken,
    getUser: getUser,
    setUser: setUser,

    // ── AUTH ──
    register: function(name, email, password) {
      return req('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name: name, email: email, password: password })
      });
    },

    login: async function(email, password) {
      var data = await req('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: email, password: password })
      });
      setToken(data.token);
      setUser(data.user);
      return data;
    },

    logout: async function() {
      await req('/auth/logout', { method: 'POST' }).catch(function() {});
      clearAuth();
    },

    me: function() {
      return req('/auth/me');
    },

    // ── FLIGHTS ──
    searchFlights: function(f, t) {
      return req('/flights?from=' + (f || '') + '&to=' + (t || ''));
    },

    adminFlights: function() {
      return req('/flights/all');
    },

    // ── BOOKINGS ──
    getMyBookings: function() {
      return req('/bookings');
    },

    myBookings: function() {
      return req('/bookings');
    },

    createBooking: function(d) {
      return req('/bookings', { method: 'POST', body: JSON.stringify(d) });
    },

    createEmergency: function(d) {
      return req('/bookings/emergency', { method: 'POST', body: JSON.stringify(d) });
    },

    createElder: function(d) {
      return req('/bookings/elder', { method: 'POST', body: JSON.stringify(d) });
    },

    cancelBooking: function(id) {
      return req('/bookings/' + id, { method: 'DELETE' });
    },

    // ── REWARDS ──
    getRewards: function() {
      return req('/rewards');
    },

    redeemReward: function(name) {
      return req('/rewards/redeem', {
        method: 'POST',
        body: JSON.stringify({ reward_name: name })
      });
    },

    // ── PROFILE ──
    updateProfile: function(d) {
      return req('/profile', { method: 'PUT', body: JSON.stringify(d) });
    },

    changePassword: function(o, n) {
      return req('/profile/password', {
        method: 'PUT',
        body: JSON.stringify({ old_password: o, new_password: n })
      });
    },

    // ── ADMIN ──
    adminDashboard: function() {
      return req('/admin/dashboard');
    },

    adminBookings: function(type) {
      return req('/admin/bookings?type=' + (type || 'all'));
    },

    adminUsers: function() {
      return req('/admin/users');
    },

    adminAnalytics: function() {
      return req('/admin/analytics');
    },

    updateFlight: function(id, d) {
      return req('/flights/' + id, { method: 'PUT', body: JSON.stringify(d) });
    }
  };
})();