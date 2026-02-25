import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

api.interceptors.request.use((config) => {
  const token = getCookie("csrftoken");
  if (token) config.headers["X-CSRFToken"] = token;
  return config;
});

export default api;