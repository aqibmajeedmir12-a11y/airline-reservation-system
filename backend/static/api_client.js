/* ═══════════════════════════════════════════════════
   SkyFlow API Client
   All calls go to /api/* on the same server
   ═══════════════════════════════════════════════════ */

window.API = (function () {
    function getToken() { return sessionStorage.getItem('sf_token') || ''; }
    function setToken(t) { sessionStorage.setItem('sf_token', t); }
    function getUser() { try { return JSON.parse(sessionStorage.getItem('sf_user')); } catch (e) { return null; } }
    function setUser(u) { sessionStorage.setItem('sf_user', JSON.stringify(u)); }
    function clearAuth() { sessionStorage.removeItem('sf_token'); sessionStorage.removeItem('sf_user'); }

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
        var json = await res.json().catch(function () { return {}; });
        if (!res.ok) {
            if (res.status === 401) {
                clearAuth();
                window.location.href = 'index_resp.html';
                throw new Error('Unauthorized');
            }
            // error may be in json.error or json.message
            var msg = json.error || json.message || ('Request failed (' + res.status + ')');
            throw new Error(msg);
        }
        return unwrap(json);
    }

    return {
        getToken: getToken,
        getUser: getUser,
        setUser: setUser,

        register: function (name, email, password) {
            return req('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ name: name, email: email, password: password })
            });
        },

        login: async function (email, password) {
            var data = await req('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email: email, password: password })
            });
            // data is already unwrapped: { token, user }
            setToken(data.token);
            setUser(data.user);
            return data;
        },

        logout: async function () {
            await req('/auth/logout', { method: 'POST' }).catch(function () { });
            clearAuth();
        },

        me: function () { return req('/auth/me'); },
        searchFlights: function (f, t) { return req('/flights?from=' + (f || '') + '&to=' + (t || '')); },
        adminFlights: function () { return req('/flights/all'); },
        getMyBookings: function () { return req('/bookings'); },
        createBooking: function (d) { return req('/bookings', { method: 'POST', body: JSON.stringify(d) }); },
        createEmergency: function (d) { return req('/bookings/emergency', { method: 'POST', body: JSON.stringify(d) }); },
        createElder: function (d) { return req('/bookings/elder', { method: 'POST', body: JSON.stringify(d) }); },
        createStudent: function (d) { return req('/bookings/student', { method: 'POST', body: JSON.stringify(d) }); },
        cancelBooking: function (id) { return req('/bookings/' + id, { method: 'DELETE' }); },
        getRewards: function () { return req('/rewards'); },
        redeemReward: function (name) { return req('/rewards/redeem', { method: 'POST', body: JSON.stringify({ reward_name: name }) }); },
        updateProfile: function (d) { return req('/profile', { method: 'PUT', body: JSON.stringify(d) }); },
        changePassword: function (o, n) { return req('/profile/password', { method: 'PUT', body: JSON.stringify({ old_password: o, new_password: n }) }); },
        adminDashboard: function () { return req('/admin/dashboard'); },
        adminBookings: function (type) { return req('/admin/bookings?type=' + (type || 'all')); },
        adminUsers: function () { return req('/admin/users'); },
        adminAnalytics: function () { return req('/admin/analytics'); },
        updateFlight: function (id, d) { return req('/flights/' + id, { method: 'PUT', body: JSON.stringify(d) }); },
        adminAddFlight: function (d) { return req('/admin/flights/add', { method: 'POST', body: JSON.stringify(d) }); },
        adminEditFlight: function (id, d) { return req('/admin/flights/' + id, { method: 'PUT', body: JSON.stringify(d) }); },
        adminDeleteFlight: function (id) { return req('/admin/flights/' + id, { method: 'DELETE' }); },
        adminCancelBooking: function (id) { return req('/admin/bookings/' + id + '/cancel', { method: 'POST' }); }
    };
})();
