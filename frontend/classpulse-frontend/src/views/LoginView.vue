<template>
  <div class="login-page">
    <!-- Left -->
    <div class="brand-panel">
      <div class="brand-content">
        <h1 class="logo">ClassPulse</h1>
        <p class="tagline">
          Organise your courses.<br />
          Track assignments.<br />
          Master your time.
        </p>
      </div>
    </div>

    <!-- Right -->
    <div class="form-panel">
      <form class="login-card" @submit.prevent="doLogin">
        <h2>Welcome Back</h2>

        <div class="form-group">
          <input
            v-model="username"
            class="input"
            placeholder="Username"
            autocomplete="username"
            required
          />
        </div>

        <div class="form-group">
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="Password"
            autocomplete="current-password"
            required
          />
        </div>

        <button
          type="submit"
          class="primary-btn"
          :disabled="loading"
        >
          {{ loading ? "Signing in..." : "Sign In" }}
        </button>

        <div class="divider"></div>

        <div class="register-row">
          <span>New to ClassPulse?</span>
          <a href="#" @click.prevent="router.push('/register')">
            Create account
          </a>
        </div>

        <div v-if="error" class="error-msg">
          {{ error }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { login } from "../auth";

const router = useRouter();
const route = useRoute();

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function doLogin() {
  error.value = "";
  loading.value = true;

  try {
    const res = await login(username.value, password.value);

    if (!res.ok) {
      throw new Error(res.error || "Login failed");
    }

    const next = route.query.next || "/";
    router.replace(next);

  } catch (e) {
    error.value =
      e?.response?.data?.error ||
      e.message ||
      "Invalid username or password.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>

.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 480px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
               "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
}

/* ===== Left Cartoon ===== */

.brand-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8vw;
  color: white;
  background: linear-gradient(
    45deg,
    #0071e3,
    #4f46e5,
    #9333ea,
    #2563eb
  );
  background-size: 300% 300%;
  animation: gradientMove 18s ease infinite;
}

@keyframes gradientMove {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.brand-content {
  max-width: 520px;
}

.logo {
  font-size: clamp(42px, 4vw, 60px);
  font-weight: 700;
  letter-spacing: -1.5px;
  margin-bottom: 24px;
  text-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

.tagline {
  font-size: clamp(16px, 1.3vw, 20px);
  line-height: 1.7;
  opacity: 0.95;
}

/* ===== Right ===== */

.form-panel {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  background: #f5f5f7;
}

/* Shadow */
.form-panel::before {
  content: "";
  position: absolute;
  left: -20px;
  top: 0;
  height: 100%;
  width: 20px;
  background: linear-gradient(
    to right,
    rgba(0,0,0,0.08),
    transparent
  );
}

/* ===== Card ===== */

.login-card {
  width: 100%;
  max-width: 360px;
  padding: 40px;
  border-radius: 22px;
  backdrop-filter: blur(25px);
  background: rgba(255,255,255,0.65);
  box-shadow: 0 30px 60px rgba(0,0,0,0.15);
}

.login-card h2 {
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 30px;
}

/* ===== Input ===== */

.form-group {
  margin-bottom: 18px;
}

.input {
  width: 100%;
  height: 48px;
  border-radius: 14px;
  border: 1px solid #e5e5ea;
  padding: 0 16px;
  font-size: 15px;
  background: rgba(255,255,255,0.9);
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.15);
}

/* ===== Button ===== */

.primary-btn {
  width: 100%;
  height: 48px;
  border-radius: 14px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  background: #0071e3;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn:hover {
  background: #005bb5;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== Register ===== */

.divider {
  height: 1px;
  background: #e5e5ea;
  margin: 26px 0;
}

.register-row {
  font-size: 14px;
  color: #6e6e73;
}

.register-row a {
  margin-left: 6px;
  color: #0071e3;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.register-row a:hover {
  text-decoration: underline;
}

.error-msg {
  margin-top: 18px;
  font-size: 14px;
  color: #d93025;
}

/* ===== Mobile ===== */

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    padding: 12vw;
  }
}

</style>