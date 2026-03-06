import api from "./api";

export async function ensureCsrf() {
  await api.get("/auth/csrf/");
}

export async function login(username, password) {
  await ensureCsrf();
  const res = await api.post("/auth/login/", { username, password });
  return res.data;
}

export async function logout() {
  const res = await api.get("/auth/logout/");
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me/");
  return res.data;
}