<template>
  <div class="wrap">
    <div class="card">
      <h1>Register</h1>
      <p class="sub">Create an account. You will be logged in automatically.</p>

      <label class="label">Username</label>
      <input class="input" v-model="username" autocomplete="username" />

      <label class="label">Password</label>
      <input class="input" v-model="password" type="password" autocomplete="new-password" />

      <label class="label">Confirm Password</label>
      <input class="input" v-model="password2" type="password" autocomplete="new-password" />

      <button class="btn" :disabled="loading" @click="doRegister">
        {{ loading ? "Creating..." : "Create account" }}
      </button>

      <div class="row">
        <span class="muted">Already have an account?</span>
        <a class="link" href="#" @click.prevent="goLogin">Login</a>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="okMsg" class="ok">{{ okMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api";
import { ensureCsrf } from "../auth";

const router = useRouter();

const username = ref("");
const password = ref("");
const password2 = ref("");
const loading = ref(false);
const error = ref("");
const okMsg = ref("");

function goLogin() {
  router.push("/login");
}

async function doRegister() {
  error.value = "";
  okMsg.value = "";
  loading.value = true;

  try {
    if (!username.value.trim()) throw new Error("Username required");
    if (password.value.length < 6) throw new Error("Password must be >= 6");
    if (password.value !== password2.value) throw new Error("Passwords do not match");

    await ensureCsrf();
    const res = await api.post("/auth/register/", {
      username: username.value,
      password: password.value,
      password2: password2.value,
    });

    if (!res.data.ok) throw new Error(res.data.error || "Register failed");

    okMsg.value = "Created! Redirecting...";
    router.replace("/");
  } catch (e) {
    error.value = e?.response?.data?.error || e.message || String(e);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.wrap { min-height: 100vh; display: grid; place-items: center; background: #f6f7fb; padding: 24px; }
.card { width: 380px; background: #fff; border: 1px solid #e8e8ee; border-radius: 16px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.04); }
h1 { margin: 0 0 6px; font-size: 20px; }
.sub { margin: 0 0 14px; color: #666; font-size: 13px; }
.label { display: block; margin: 10px 0 6px; font-size: 13px; color: #333; }
.input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 12px; outline: none; }
.input:focus { border-color: #aaa; }
.btn { width: 100%; margin-top: 14px; padding: 10px 12px; border: none; border-radius: 12px; cursor: pointer; background: #111; color: #fff; }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.row { margin-top: 12px; display: flex; justify-content: center; gap: 8px; font-size: 13px; }
.muted { color: #666; }
.link { color: #2563eb; text-decoration: none; }
.link:hover { text-decoration: underline; }
.error { margin-top: 10px; color: #b91c1c; font-size: 13px; text-align: center; }
.ok { margin-top: 10px; color: #15803d; font-size: 13px; text-align: center; }
</style>