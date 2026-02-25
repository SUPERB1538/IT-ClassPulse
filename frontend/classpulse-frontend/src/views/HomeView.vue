<template>
  <div class="page">
    <!-- Top bar -->
    <header class="topbar">
      <div class="brand">ClassPulse</div>
      <div class="right">
        <span v-if="me" class="user">{{ me.username }}</span>
        <a v-if="me" href="#" @click.prevent="logoutNow" class="link">Logout</a>
      </div>
    </header>

    <main class="main">
      <!-- Left cards -->
      <section class="left">
        <div class="card" @click="go('/courses')">
          <div class="card-title">Courses</div>
          <div class="card-sub">Browse and manage your courses.</div>
          <div class="card-action">View all →</div>
        </div>

        <div class="card" @click="go('/assignments')">
          <div class="card-title">Assignments</div>
          <div class="card-sub">Check deadlines and progress.</div>
          <div class="card-action">View all →</div>
        </div>

        <div class="card" @click="go('/studyplans')">
          <div class="card-title">Study Plans</div>
          <div class="card-sub">Plan your study hours by day.</div>
          <div class="card-action">View all →</div>
        </div>

        <div v-if="error" class="error">{{ error }}</div>
      </section>

      <!-- Timetable -->
      <section class="board">
        <div class="board-header">
          <div class="board-title">Your Timetable</div>
          <a class="link" href="#" @click.prevent="onAddSession">+ Add class session</a>
        </div>

        <div v-if="loading" class="muted pad">Loading timetable...</div>

        <div class="table-wrap" v-else-if="dashboard">
          <div style="overflow-x: auto;">
            <table class="timetable">
              <thead>
                <tr>
                  <th class="col-time">Time</th>
                  <th v-for="d in dashboard.days" :key="d[0]">{{ d[1] }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in dashboard.rows" :key="row[0]">
                  <td class="time">{{ row[0] }}</td>

                  <template v-for="(cell, idx) in row[1]" :key="idx">
                    <!-- skip 占位（rowspan 下方格子不渲染） -->
                    <td v-if="cell && cell.skip" style="display:none;"></td>

                    <!-- 空格 -->
                    <td v-else-if="!cell" class="empty"></td>

                    <!-- 有课 -->
                    <td
                      v-else
                      class="session"
                      :rowspan="cell.rowspan"
                      @click="onSessionClick(cell)"
                    >
                      <div class="session-text">
                        <div v-for="(line, i) in splitLines(cell.text)" :key="i">
                          {{ line }}
                        </div>
                      </div>
                    </td>
                  </template>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else class="muted pad">
          No timetable data.
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "../api";
import { logout as doLogout, getMe, ensureCsrf } from "../auth";

const router = useRouter();

const me = ref(null);
const dashboard = ref(null);
const loading = ref(true);
const error = ref("");

function splitLines(text) {
  return String(text || "").split("\n");
}

function go(path) {
  // 你现在可能还没做 /courses /assignments /studyplans 页面
  // 这里先跳转，路由没配会 404，之后我也能给你补齐
  router.push(path);
}

function onAddSession() {
  alert("后面可以做一个新增课表页面：/sessions/new（我也能给你完整代码）");
}

function onSessionClick(cell) {
  alert(`session id: ${cell.session_id}\n${cell.text}`);
}

async function logoutNow() {
  error.value = "";
  try {
    await doLogout();
    router.replace("/login");
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : String(e);
  }
}

async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    // 确保有 csrftoken cookie（对 session + POST 更稳）
    await ensureCsrf();

    // 当前用户
    const m = await getMe();
    if (!m?.ok) {
      router.replace("/login");
      return;
    }
    me.value = m;

    // dashboard 数据
    const res = await api.get("/dashboard/");
    dashboard.value = res.data;
  } catch (e) {
    // 通常是未登录 403，或者 CORS/CSRF 没配好
    const status = e?.response?.status;
    if (status === 403 || status === 401) {
      router.replace("/login");
      return;
    }
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fff;
}

.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid #eee;
}

.brand {
  font-weight: 600;
}

.right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user {
  color: #222;
}

.link {
  color: #3b82f6;
  text-decoration: none;
  cursor: pointer;
}
.link:hover {
  text-decoration: underline;
}

.muted {
  color: #666;
}
.pad {
  padding: 12px 14px 14px 14px;
}

.main {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 22px;
  padding: 24px 22px;
  max-width: 1200px;
  margin: 0 auto;
}

/* left cards */
.left .card {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 14px;
  cursor: pointer;
  background: #fff;
}
.left .card:hover {
  border-color: #d4d4d4;
}
.card-title {
  font-weight: 700;
  margin-bottom: 4px;
}
.card-sub {
  color: #666;
  font-size: 13px;
}
.card-action {
  margin-top: 10px;
  color: #666;
  font-size: 13px;
  text-align: right;
}

/* board */
.board {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  background: #fff;
}
.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 14px 8px 14px;
}
.board-title {
  font-weight: 700;
}
.table-wrap {
  padding: 0 14px 14px 14px;
}

.timetable {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.timetable th,
.timetable td {
  border: 1px solid #e3e3e3;
  padding: 0;
}
.col-time {
  width: 80px;
}
.time {
  font-weight: 600;
  font-size: 12px;
  text-align: center;
  background: #fafafa;
}
.empty {
  height: 28px;
  background: #fff;
}
.session {
  background: #eef6ff;
  vertical-align: middle;
  cursor: pointer;
}
.session-text {
  padding: 10px;
  font-size: 12px;
  line-height: 1.25;
  white-space: pre-line;
}

.error {
  margin-top: 10px;
  color: #b91c1c;
  font-size: 13px;
}
</style>