import axios from "axios";

// Central axios instance keeps API URLs relative so the frontend
// can work across environments without hard-coded absolute paths.
const api = axios.create({
  baseURL: "https://classpulse-twdk.onrender.com/api",
  withCredentials: true,
});

function getCookie(name) {
  // Read Django's CSRF cookie so write requests can include it automatically.
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

api.interceptors.request.use((config) => {
  // Attach the CSRF token to every outgoing request that may need it.
  const token = getCookie("csrftoken");
  if (token) config.headers["X-CSRFToken"] = token;
  return config;
});

export default api;