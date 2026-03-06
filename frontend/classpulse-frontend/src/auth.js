import api from "./api";

export async function ensureCsrf() {
  const res = await api.get("/auth/csrf/");
  const token = res.data?.csrfToken;
  if (token) {
    api.defaults.headers.common["X-CSRFToken"] = token;
  }
  return token;
}

export async function login(username, password) {
  await ensureCsrf();
  const res = await api.post("/auth/login/", { username, password });
  return res.data;
}

export async function logout() {
  await ensureCsrf();
  const res = await api.post("/auth/logout/");
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me/");
  return res.data;
}