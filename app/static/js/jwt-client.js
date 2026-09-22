/**
 * JWTClient — fetch wrapper com Bearer auto-inject e logout em 401.
 */
class JWTClient {
  static async fetch(url, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      const refreshed = await JWTClient._refresh();
      if (refreshed) {
        headers["Authorization"] =
          `Bearer ${localStorage.getItem("access_token")}`;
        res = await fetch(url, { ...options, headers });
      }
      if (res.status === 401) {
        JWTClient.logout();
        return res;
      }
    }
    return res;
  }

  static async _refresh() {
    const rt = localStorage.getItem("refresh_token");
    if (!rt) return false;
    try {
      const res = await fetch("/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  static logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    document.cookie =
      "admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    document.cookie =
      "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    window.location.href = "/admin/login";
  }
}
