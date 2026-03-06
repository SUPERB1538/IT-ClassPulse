<template>
  <div class="register-page">

    <!-- Left -->
    <div class="brand-panel">
      <div class="brand-content">
        <h1 class="logo">ClassPulse</h1>
        <p class="tagline">
          Organise your courses.<br>
          Track assignments.<br>
          Master your time.
        </p>
      </div>
    </div>

    <!-- Right -->
    <div class="form-panel">
      <form class="register-card" @submit.prevent="doRegister">

        <h2>Create Account</h2>

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
            autocomplete="new-password"
            required
          />
        </div>

        <div class="form-group">
          <input
            v-model="password2"
            type="password"
            class="input"
            placeholder="Confirm password"
            autocomplete="new-password"
            required
          />
        </div>

        <button
          type="submit"
          class="primary-btn"
          :disabled="loading"
        >
          {{ loading ? "Creating..." : "Create Account" }}
        </button>

        <div class="divider"></div>

        <div class="login-row">
          <span>Already have an account?</span>
          <a href="#" @click.prevent="goLogin">Sign in</a>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="okMsg" class="ok-msg">{{ okMsg }}</div>

      </form>
    </div>

  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import api from "../api"
import { ensureCsrf } from "../auth"

const router = useRouter()

const username = ref("")
const password = ref("")
const password2 = ref("")
const loading = ref(false)
const error = ref("")
const okMsg = ref("")

function goLogin(){
  router.push("/login")
}

async function doRegister(){

  error.value=""
  okMsg.value=""
  loading.value=true

  try{

    if(!username.value.trim())
      throw new Error("Username required")

    if(password.value.length < 6)
      throw new Error("Password must be at least 6 characters")

    if(password.value !== password2.value)
      throw new Error("Passwords do not match")

    await ensureCsrf()

    const res = await api.post("/auth/register/",{
      username: username.value,
      password: password.value,
      password2: password2.value
    })

    if(!res.data.ok)
      throw new Error(res.data.error || "Register failed")

    okMsg.value="Account created! Redirecting..."

    router.replace("/")

  }catch(e){

    error.value =
      e?.response?.data?.error ||
      e.message ||
      "Register failed"

  }finally{
    loading.value=false
  }

}
</script>

<style scoped>

/* Page */

.register-page{
  min-height:100vh;
  display:grid;
  grid-template-columns:1fr 480px;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display",
  "SF Pro Text","Helvetica Neue",Arial,sans-serif;
}

/* Left */

.brand-panel{
  display:flex;
  align-items:center;
  justify-content:center;
  padding:8vw;
  color:white;

  background:linear-gradient(
    45deg,
    #0071e3,
    #4f46e5,
    #9333ea,
    #2563eb
  );

  background-size:300% 300%;
  animation:gradientMove 18s ease infinite;
}

@keyframes gradientMove{
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}

.brand-content{
  max-width:520px;
}

.logo{
  font-size:clamp(42px,4vw,60px);
  font-weight:700;
  letter-spacing:-1.5px;
  margin-bottom:24px;
}

.tagline{
  font-size:clamp(16px,1.3vw,20px);
  line-height:1.7;
  opacity:.95;
}

/* Right */

.form-panel{
  position:relative;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:60px 40px;
  background:#f5f5f7;
}

.form-panel::before{
  content:"";
  position:absolute;
  left:-20px;
  top:0;
  height:100%;
  width:20px;

  background:linear-gradient(
    to right,
    rgba(0,0,0,.08),
    transparent
  );
}

/* Card */

.register-card{
  width:100%;
  max-width:360px;
  padding:40px;

  border-radius:22px;

  backdrop-filter:blur(25px);
  background:rgba(255,255,255,.65);

  box-shadow:0 30px 60px rgba(0,0,0,.15);
}

.register-card h2{
  font-size:26px;
  font-weight:600;
  margin-bottom:30px;
}

/* Input */

.form-group{
  margin-bottom:16px;
}

.input{
  width:100%;
  height:48px;
  border-radius:14px;
  border:1px solid #e5e5ea;

  padding:0 16px;
  font-size:15px;

  background:rgba(255,255,255,.9);
}

.input:focus{
  outline:none;
  border-color:#0071e3;
  box-shadow:0 0 0 3px rgba(0,113,227,.15);
}

/* Button */

.primary-btn{
  width:100%;
  height:48px;

  border-radius:14px;
  border:none;

  font-size:15px;
  font-weight:600;

  background:#0071e3;
  color:white;

  cursor:pointer;
}

.primary-btn:hover{
  background:#005bb5;
}

.primary-btn:disabled{
  opacity:.6;
}

/* Other */

.divider{
  height:1px;
  background:#e5e5ea;
  margin:26px 0;
}

.login-row{
  font-size:14px;
  color:#6e6e73;
}

.login-row a{
  margin-left:6px;
  color:#0071e3;
  text-decoration:none;
}

.login-row a:hover{
  text-decoration:underline;
}

.error-msg{
  margin-top:18px;
  font-size:14px;
  color:#d93025;
}

.ok-msg{
  margin-top:18px;
  font-size:14px;
  color:#16a34a;
}
</style>