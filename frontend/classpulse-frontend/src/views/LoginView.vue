<template>
  <div class="wrap">
    <div class="card">
      <h1>Login</h1>
      <p class="sub">Use your Django user account (same as admin).</p>

      <label class="label">Username</label>
      <input class="input" v-model="username" placeholder="e.g. admin" />

      <label class="label">Password</label>
      <input class="input" v-model="password" type="password" placeholder="••••••••" />

      <button class="btn" :disabled="loading" @click="doLogin">
        {{ loading ? "Logging in..." : "Login" }}
      </button>

      <div class="row">
        <span class="muted">No account?</span>
        <a class="link" href="#" @click.prevent="router.push('/register')">Register</a>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
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
    if (!res.ok) throw new Error(res.error || "Login failed");

    const next = route.query.next || "/";
    router.replace(next);
  } catch (e) {
    error.value = e?.response?.data?.error || e.message || String(e);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #fff;
}
.card {
  width: 360px;
  border: 1px solid #e6e6e6;
  border-radius: 14px;
  padding: 18px;
}
h1 {
  margin: 0 0 6px 0;
  font-size: 20px;
}
.sub {
  margin: 0 0 14px 0;
  color: #666;
  font-size: 13px;
}
.label {
  display: block;
  margin: 10px 0 6px 0;
  font-size: 13px;
  color: #333;
}
.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 10px;
  outline: none;
}
.input:focus { border-color: #bbb; }
.btn {
  width: 100%;
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 10px;
  cursor: pointer;
  background: #111;
  color: #fff;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  margin-top: 10px;
  color: #b91c1c;
  font-size: 13px;
}
</style>