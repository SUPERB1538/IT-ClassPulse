<template>
  <div class="page dashboard-page">
    <!-- ===== Topbar ===== -->
    <header class="topbar">
      <div class="brand">ClassPulse</div>

      <div class="right">
        <div v-if="me" class="user-wrapper">
          <div class="avatar-container" @click.stop="toggleMenu">
            <div class="avatar" :style="{ backgroundColor: avatarColor }">
              {{ userInitial }}
            </div>
            <div class="arrow" :class="{ open: menuOpen }"></div>
          </div>

          <div v-if="menuOpen" class="dropdown">
            <div class="dropdown-item danger" @click="logoutNow">Logout</div>
          </div>
        </div>
      </div>
    </header>

    <!-- ===== Main Layout ===== -->
    <main class="main">
      <!-- Left Panel -->
      <section class="left">
        <div class="card" @click="go('/courses')">
          <div class="card-content">
            <div>
              <div class="card-title">Courses</div>
              <div class="card-sub">Browse and manage your courses.</div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card" @click="go('/assignments')">
          <div class="card-content">
            <div>
              <div class="card-title">Assignments</div>
              <div class="card-sub">Check deadlines and progress.</div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card" @click="go('/studyplans')">
          <div class="card-content">
            <div>
              <div class="card-title">Study Plans</div>
              <div class="card-sub">Plan your study days before deadlines.</div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>
      </section>

      <!-- Timetable -->
      <section class="board">
        <div class="board-header">
          <div class="board-title">Your Timetable</div>
          <a class="link" href="#" @click.prevent="onAddSession">+ Add class session</a>
        </div>

        <div v-if="loading" class="pad muted">Loading timetable...</div>

        <div v-else-if="dashboard" class="table-wrap">
          <div style="overflow-x:auto;">
            <table class="modern-table">
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
                    <td v-if="cell && cell.skip" style="display:none;"></td>
                    <td v-else-if="!cell" class="empty"></td>

                    <td
                      v-else
                      class="session"
                      :rowspan="cell.rowspan"
                      @click="onSessionClick(cell)"
                    >
                      <div class="session-text">{{ cell.text }}</div>
                    </td>
                  </template>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else class="pad muted">No timetable data.</div>
      </section>
    </main>

    <!-- ===== Add Class Session Modal ===== -->
    <div v-if="showAddSession" class="modal-mask" @click.self="showAddSession = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Add class session</div>
          <button class="iconbtn" @click="showAddSession = false">✕</button>
        </div>

        <div class="form-row">
          <label>Course</label>
          <select v-model="sessionForm.course" class="input">
            <option value="" disabled>Select course</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">
              {{ c.course_name }}
            </option>
          </select>
        </div>

        <div class="form-row">
          <label>Day</label>
          <select v-model="sessionForm.day_of_week" class="input">
            <option :value="1">Mon</option>
            <option :value="2">Tue</option>
            <option :value="3">Wed</option>
            <option :value="4">Thu</option>
            <option :value="5">Fri</option>
            <option :value="6">Sat</option>
            <option :value="7">Sun</option>
          </select>
        </div>

        <div class="grid2">
          <div class="form-row">
            <label>Start</label>
            <input type="time" v-model="sessionForm.start_time" class="input" />
          </div>
          <div class="form-row">
            <label>End</label>
            <input type="time" v-model="sessionForm.end_time" class="input" />
          </div>
        </div>

        <div class="form-row">
          <label>Location</label>
          <input v-model="sessionForm.location" class="input" placeholder="Optional" />
        </div>

        <div v-if="sessionError" class="error">{{ sessionError }}</div>

        <div class="modal-actions">
          <button class="btn ghost" @click="showAddSession = false">Cancel</button>
          <button class="btn" :disabled="!sessionForm.course || addingSession" @click="addClassSession">
            {{ addingSession ? "Adding..." : "Add" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../api";
import { logout as doLogout, getMe, ensureCsrf } from "../auth";

const router = useRouter();

const me = ref(null);
const dashboard = ref(null);
const loading = ref(true);

const menuOpen = ref(false);

/* ===== Modal state ===== */
const showAddSession = ref(false);
const courses = ref([]);
const sessionError = ref("");
const addingSession = ref(false);

const sessionForm = ref({
  course: "",
  day_of_week: 1,
  start_time: "09:00",
  end_time: "10:00",
  location: "",
});

/* ===== 首字母 ===== */
const userInitial = computed(() => {
  if (!me.value?.username) return "";
  return me.value.username.charAt(0).toUpperCase();
});

/* ===== 稳定随机颜色 ===== */
function stringToColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 55%)`;
}

const avatarColor = computed(() => {
  if (!me.value?.username) return "#0071e3";
  return stringToColor(me.value.username);
});

/* ===== 菜单控制 ===== */
function toggleMenu() {
  menuOpen.value = !menuOpen.value;
}

function handleClickOutside(event) {
  const wrapper = document.querySelector(".user-wrapper");
  if (wrapper && !wrapper.contains(event.target)) {
    menuOpen.value = false;
  }
}

function go(path) {
  menuOpen.value = false;
  router.push(path);
}

async function logoutNow() {
  menuOpen.value = false;
  await doLogout();
  router.replace("/login");
}

/* ===== data loading ===== */
async function loadAll() {
  loading.value = true;
  await ensureCsrf();

  const m = await getMe();
  if (!m?.ok) {
    router.replace("/login");
    return;
  }
  me.value = m;

  const res = await api.get("/dashboard/");
  dashboard.value = res.data;

  loading.value = false;
}

async function loadCourses() {
  const res = await api.get("/courses/");
  courses.value = res.data || [];
  if (!sessionForm.value.course && courses.value.length) {
    sessionForm.value.course = courses.value[0].id;
  }
}

/* ===== add session ===== */
async function onAddSession() {
  sessionError.value = "";
  showAddSession.value = true;

  try {
    await loadCourses();
  } catch (e) {
    sessionError.value = "Failed to load courses";
  }
}

function onSessionClick(cell) {
  // 你后续可以换成自定义 modal，这里先保留调试信息
  alert(`session id: ${cell.session_id}\n${cell.text}`);
}

async function addClassSession() {
  sessionError.value = "";
  addingSession.value = true;

  try {
    await ensureCsrf();

    await api.post("/sessions/", {
      course: sessionForm.value.course,
      day_of_week: Number(sessionForm.value.day_of_week),
      start_time: sessionForm.value.start_time,
      end_time: sessionForm.value.end_time,
      location: sessionForm.value.location || "",
    });

    showAddSession.value = false;

    // refresh dashboard
    const dashRes = await api.get("/dashboard/");
    dashboard.value = dashRes.data;
  } catch (e) {
    const data = e?.response?.data;
    sessionError.value = data
      ? (data.overlap || data.time || data.detail || JSON.stringify(data))
      : (e.message || String(e));
  } finally {
    addingSession.value = false;
  }
}

onMounted(() => {
  loadAll();
  document.addEventListener("click", handleClickOutside);
});
</script>

<style scoped>
/* ===== Page ===== */
.dashboard-page {
  min-height: 100vh;
  background: #f5f5f7;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
    "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ===== Topbar ===== */
.topbar {
  height: 64px;
  padding: 0 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #e5e5e7;
}

.brand {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.right {
  display: flex;
  align-items: center;
}

/* ===== Layout ===== */
.main {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 32px;
  padding: 48px 64px;
  max-width: 1600px;
  margin: 0 auto;
}

/* ===== Cards ===== */
.left .card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  padding: 22px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 20px 40px rgba(0, 0, 0, 0.06);
  transition: all 0.25s ease;
  cursor: pointer;
}

.left .card:hover {
  transform: translateY(-4px);
}

.card-content {
  display: flex;
  justify-content: space-between;
  gap: 18px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.card-sub {
  font-size: 15px;
  color: #6e6e73;
  line-height: 1.5;
}

.card-action {
  height: fit-content;
  margin-top: 2px;
  font-size: 14px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f2f2f7;
  color: #0071e3;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.left .card:hover .card-action {
  background: #e8e8ef;
}

/* ===== Board ===== */
.board {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05), 0 30px 80px rgba(0, 0, 0, 0.06);
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.board-title {
  font-size: 22px;
  font-weight: 600;
}

.table-wrap {
  margin-top: 8px;
}

.pad {
  padding: 12px 0;
}

.muted {
  color: #6e6e73;
}

.link {
  color: #0071e3;
  text-decoration: none;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

/* ===== Timetable ===== */
.modern-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
  overflow: hidden;
  border-radius: 16px;
}

.col-time {
  width: 90px;
}

.modern-table th {
  background: #f2f2f7;
  color: #6e6e73;
  font-weight: 500;
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.modern-table td {
  border: 1px solid #f2f2f7;
  padding: 0;
}

.time {
  font-weight: 500;
  color: #6e6e73;
  background: #fafafa;
  text-align: center;
  padding: 10px 8px !important;
}

.empty {
  height: 36px;
  background: rgba(255, 255, 255, 0.6);
  transition: background 0.15s ease;
}

.empty:hover {
  background: rgba(0, 113, 227, 0.06);
}

.session {
  background: rgba(0, 113, 227, 0.12);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;

  display: flex;
  align-items: center;
  justify-content: center;
}

.session:hover {
  background: rgba(0, 113, 227, 0.2);
  transform: translateY(-1px);
}

.session-text {
  padding: 10px;
  text-align: center;
  white-space: pre-line;

  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;

  color: #1d1d1f;
}

/* ===== Avatar ===== */
.user-wrapper {
  position: relative;
}

.avatar-container {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.arrow {
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid #6e6e73;
  transition: transform 0.2s ease;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown {
  position: absolute;
  top: 55px;
  right: 0;
  width: 180px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
}

.dropdown-item {
  padding: 10px 16px;
  font-size: 14px;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #f2f2f7;
}

.dropdown-item.danger {
  color: #dc2626;
}

.dropdown-divider {
  height: 1px;
  background: #e5e5e7;
  margin: 6px 0;
}

/* ===== Modal ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  display: grid;
  place-items: center;
  padding: 24px;
  z-index: 50;
}

.modal {
  width: 460px;
  max-width: 100%;
  border-radius: 20px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(229, 229, 231, 0.9);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.iconbtn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  color: #6e6e73;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 12px 0;
}

.form-row label {
  font-size: 13px;
  color: #6e6e73;
}

.input {
  height: 40px;
  border-radius: 14px;
  border: 1px solid rgba(229, 229, 231, 0.9);
  padding: 0 12px;
  outline: none;
  background: rgba(255, 255, 255, 0.8);
}

.input:focus {
  border-color: rgba(0, 113, 227, 0.55);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
}

.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

.btn {
  height: 40px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid rgba(229, 229, 231, 0.9);
  background: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  transition: transform 0.15s ease, background 0.15s ease;
}

.btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.95);
}

.btn.ghost {
  background: rgba(245, 245, 247, 0.9);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.error {
  margin-top: 8px;
  color: #dc2626;
  font-size: 13px;
}
</style>