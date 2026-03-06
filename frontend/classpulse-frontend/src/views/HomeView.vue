<template>
  <div class="page dashboard-page">
    <!-- ===== Topbar ===== -->
    <header class="topbar">
      <div class="brand">ClassPulse</div>

      <div class="right">
        <div v-if="me" class="user-wrapper">
          <div class="avatar-container"
                tabindex="0"
                role="button"
                aria-haspopup="menu"
                :aria-expanded="menuOpen"
                @click.stop="toggleMenu"
                @keydown.enter.prevent="toggleMenu"
                @keydown.space.prevent="toggleMenu"
                @keydown.esc.prevent="menuOpen=false">
            <div class="avatar" :style="{ backgroundColor: avatarColor }">
              {{ userInitial }}
            </div>
            <div class="arrow" :class="{ open: menuOpen }"></div>
          </div>

          <div v-if="menuOpen" class="dropdown">
            <div class="dropdown-item danger"
                  role="menuitem"
                  tabindex="0"
                  @click="logoutNow"
                  @keydown.enter.prevent="logoutNow"
                  @keydown.space.prevent="logoutNow">Logout</div>
          </div>
        </div>
      </div>
    </header>

    <!-- ===== Main Layout ===== -->
    <main class="main">
      <!-- Left Panel -->
      <section class="left">
        <div class="card"
              role="button"
              tabindex="0"
              @click="go('/courses')"
              @keydown.enter.prevent="go('/courses')"
              @keydown.space.prevent="go('/courses')">
          <div class="card-content">
            <div>
              <div class="card-title">Courses</div>
              <div class="card-sub">Browse and manage your courses.</div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card"
              role="button"
              tabindex="0"
              @click="go('/assignments')"
              @keydown.enter.prevent="go('/assignments')"
              @keydown.space.prevent="go('/assignments')">
          <div class="card-content">
            <div>
              <div class="card-title">Assignments</div>
              <div class="card-sub">Check deadlines and progress.</div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card studyplan-card"
              role="button"
              tabindex="0"
              @click="go('/studyplans')"
              @keydown.enter.prevent="go('/studyplans')"
              @keydown.space.prevent="go('/studyplans')">
          <div class="card-content">
            <div>
              <div class="card-title">Study Plans</div>
              <div class="card-sub">Plan your study days before deadlines.</div>
            </div>
            <div class="card-action">View all</div>
          </div>

          <!-- read-only preview -->
          <div class="studyplan-preview" @click.stop>
            <div v-if="loadingPlans" class="muted preview-empty">Loading...</div>

            <div v-else-if="previewPlans.length === 0" class="muted preview-empty">
              No study plans.
            </div>

            <ul v-else class="preview-list">
              <li v-for="p in previewPlans" :key="p.id" class="preview-item">
                <div class="preview-leftcol">
                  <div class="preview-info">
                    <div class="preview-line1">{{ p.assignment_title }}</div>

                    <div class="preview-line2 muted">
                      Course: {{ p.course_name }}
                    </div>

                    <div class="preview-line3">
                      <span class="muted">Due:</span>
                      <span :class="['due', previewDueClass(p)]">
                        {{ previewDueText(p) }}
                      </span>
                    </div>

                    <div class="preview-line4">
                      <span class="muted">Plan:</span>
                      <span>{{ p.plan_duration_human }}</span>

                      <span class="muted">• Countdown:</span>
                      <span :class="['countdown', previewCountdownClass(p)]">
                        {{ previewCountdownText(p) }}
                      </span>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
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
                    <template v-if="cell && cell.skip"></template>

                    <td v-else-if="!cell" class="empty"></td>

                    <td
                      v-else
                      class="session"
                      :rowspan="cell.rowspan"
                      tabindex="0"
                      role="button"
                      :aria-label="`Session ${cell.text}`"
                      @click="onSessionClick(cell)"
                      @keydown.enter.prevent="onSessionClick(cell)"
                      @keydown.space.prevent="onSessionClick(cell)"
                      title="Click to edit"
                    >
                    <div class="session-text">
                      <div class="session-title">{{ cell.title }}</div>
                      <div class="session-subtitle" :title="cell.subtitle">
                        {{ cell.subtitle }}
                      </div>
                    </div>
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
          <div class="modal-title">{{ modalMode === "add" ? "Add class session" : "Edit class session" }}</div>
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
          <button
            v-if="modalMode === 'edit'"
            class="btn ghost danger"
            @click="deleteSession"
          >
            Delete
          </button>

          <button class="btn ghost" @click="showAddSession = false">
            Cancel
          </button>

          <button
            class="btn"
            :disabled="!sessionForm.course || addingSession"
            @click="addClassSession"
          >
            {{ addingSession ? "Saving..." : (modalMode === "add" ? "Add" : "Save") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import api from "../api";
import { logout as doLogout, getMe, ensureCsrf } from "../auth";

const router = useRouter();

const me = ref(null);
const dashboard = ref(null);
const loading = ref(true);

/* ===== Study plan preview ===== */
const studyPlans = ref([]);
const loadingPlans = ref(false);

const previewNowMs = ref(Date.now());
let previewTimer = null;

// Persist countdown start times locally so the study-plan timer
// continues consistently across refreshes within the same browser.
const START_KEY = "studyplan_start_times_v1";

function loadPreviewStartTimes() {
  try {
    return JSON.parse(localStorage.getItem(START_KEY) || "{}");
  } catch {
    return {};
  }
}

const previewStartTimes = ref(loadPreviewStartTimes());

function savePreviewStartTimes() {
  localStorage.setItem(START_KEY, JSON.stringify(previewStartTimes.value));
}

function ensurePreviewStartTime(planId) {
  // Create a stable start time the first time a plan is seen.
  // Without this, the countdown would restart on every reload.
  if (!planId) return Date.now();
  if (!previewStartTimes.value[planId]) {
    previewStartTimes.value[planId] = Date.now();
    savePreviewStartTimes();
  }
  return previewStartTimes.value[planId];
}

async function fetchStudyPlans() {
  loadingPlans.value = true;
  try {
    const res = await api.get("/studyplans/");
    studyPlans.value = res.data || [];
    studyPlans.value.forEach((p) => ensurePreviewStartTime(p.id));
  } catch (e) {
    studyPlans.value = [];
  } finally {
    loadingPlans.value = false;
  }
}

// Only show active study plans in the homepage preview:
// completed or overdue work is excluded from the countdown panel.
const previewPlans = computed(() =>
  studyPlans.value.filter((p) => {
    const status = (p.assignment_status || "").toLowerCase();
    return p.time_left_seconds > 0 && status !== "completed";
  })
);

function formatSeconds(secs) {
  if (secs <= 0) return "Overdue";
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const mins = Math.floor((secs % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

function previewDueText(p) {
  if (p.time_left_human) return p.time_left_human;
  if (typeof p.time_left_seconds === "number") return formatSeconds(p.time_left_seconds);
  return "N/A";
}

function previewDueClass(p) {
  const secs = Number(p.time_left_seconds);
  if (!Number.isFinite(secs)) return "ok";
  if (secs <= 0) return "bad";
  if (secs <= 86400) return "warn";
  return "ok";
}

function previewCountdownSeconds(p) {
  // Countdown is based on the locally stored start time plus
  // the planned study duration returned by the backend.
  const start = ensurePreviewStartTime(p.id);
  const total = Number(p.plan_duration_seconds || 86400);
  const left = Math.floor((start + total * 1000 - previewNowMs.value) / 1000);
  return left;
}

function formatHMS(secs) {
  if (secs <= 0) return "Time up";

  const days = Math.floor(secs / 86400);
  const rem = secs % 86400;

  const h = Math.floor(rem / 3600);
  const m = Math.floor((rem % 3600) / 60);
  const s = Math.floor(rem % 60);

  const hh = String(h).padStart(2, "0");
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");

  if (days <= 0) return `${hh}:${mm}:${ss}`;
  return `${days}d ${hh}:${mm}:${ss}`;
}

function previewCountdownText(p) {
  return formatHMS(previewCountdownSeconds(p));
}

function previewCountdownClass(p) {
  const left = previewCountdownSeconds(p);
  if (left <= 0) return "bad";
  if (left <= 3600) return "warn";
  return "ok";
}

function handleStudyPlansChanged() {
  fetchStudyPlans();
}

const menuOpen = ref(false);

const modalMode = ref("add"); 
const editingSessionId = ref(null);

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

/* ===== First name ===== */
const userInitial = computed(() => {
  if (!me.value?.username) return "";
  return me.value.username.charAt(0).toUpperCase();
});

/* ===== Color ===== */
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

/* ===== menu ===== */
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
  modalMode.value = "add";
  editingSessionId.value = null;
  sessionForm.value = {
    course: "",
    day_of_week: 1,
    start_time: "09:00",
    end_time: "10:00",
    location: "",
  };

  showAddSession.value = true;

  try {
    await loadCourses();
  } catch (e) {
    sessionError.value = "Failed to load courses";
  }
}

async function deleteSession() {
  if (!editingSessionId.value) return;
  const ok = confirm("Delete this class session?");
  if (!ok) return;
  try {
    await ensureCsrf();
    await api.delete(`/sessions/${editingSessionId.value}/`);
    const dashRes = await api.get("/dashboard/");
    dashboard.value = dashRes.data;
    showAddSession.value = false;
  } catch (e) {
    sessionError.value = "Failed to delete session.";
  }
}

async function onSessionClick(cell) {
  sessionError.value = "";
  modalMode.value = "edit";
  editingSessionId.value = cell.session_id;

  showAddSession.value = true;

  try {
    await ensureCsrf();
    await loadCourses();
    const res = await api.get(`/sessions/${cell.session_id}/`);
    const s = res.data;

    sessionForm.value = {
      course: String(s.course), 
      day_of_week: Number(s.day_of_week),
      start_time: s.start_time?.slice(0,5) || "09:00",
      end_time: s.end_time?.slice(0,5) || "10:00",
      location: s.location || "",
    };
  } catch (e) {
    sessionError.value = "Failed to load this session.";
  }
}

async function addClassSession() {
  sessionError.value = "";
  addingSession.value = true;

  try {
    await ensureCsrf();

    const payload = {
      course: Number(sessionForm.value.course),
      day_of_week: Number(sessionForm.value.day_of_week),
      start_time: sessionForm.value.start_time,
      end_time: sessionForm.value.end_time,
      location: sessionForm.value.location || "",
    };

    if (modalMode.value === "add") {
      await api.post("/sessions/", payload);
    } else {
      await api.patch(`/sessions/${editingSessionId.value}/`, payload);
    }

    // refresh dashboard
    const dashRes = await api.get("/dashboard/");
    dashboard.value = dashRes.data;
    // close modal
    showAddSession.value = false;
    menuOpen.value = false;
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
  fetchStudyPlans();

  previewTimer = setInterval(() => {
    previewNowMs.value = Date.now();
  }, 1000);

  document.addEventListener("click", handleClickOutside);
  window.addEventListener("studyplans:changed", handleStudyPlansChanged);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
  window.removeEventListener("studyplans:changed", handleStudyPlansChanged);

  if (previewTimer) clearInterval(previewTimer);
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
  table-layout: fixed;
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

  vertical-align: middle;
  text-align: center;
}

.session:hover {
  background: rgba(0, 113, 227, 0.2);
  transform: translateY(-1px);
}

.session-text{
  padding: 10px;
  text-align: center;
}

.session-title{
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.session-subtitle{
  margin-top: 2px;
  font-size: 12px;
  font-weight: 500;
  color: #6e6e73;
  display: -webkit-box;
  -webkit-line-clamp: 2; 
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

.btn.danger {
  color: #dc2626;
}

.btn.danger:hover {
  background: rgba(220,38,38,0.08);
}

/* ===== Study plan preview on dashboard ===== */
.studyplan-card {
  overflow: hidden;
}

.studyplan-preview {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #eef0f3;
}

.preview-empty {
  font-size: 13px;
}

.preview-list {
  list-style: none;
  padding: 0;
  margin: 0;
  margin-top: 10px;
  max-height: 520px;
  overflow-y: auto;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  border: 1px solid #eee;
  margin-bottom: 12px;
  background: #f8fafc;
}

.preview-leftcol {
  flex: 1;
  min-width: 0;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-line1 {
  font-weight: 700;
  font-size: 15px;
  color: #111827;
}

.preview-line2 {
  font-size: 13px;
}

.preview-line3,
.preview-line4 {
  font-size: 13px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.due.ok,
.countdown.ok {
  color: #111827;
}

.due.bad {
  color: #dc2626;
  font-weight: 600;
}

.due.warn {
  color: #dc2626;
  font-weight: 700;
}

.countdown.warn {
  color: #b45309;
  font-weight: 700;
}

.countdown.bad {
  color: #dc2626;
  font-weight: 800;
}


/* ===== Mobile dashboard final fix ===== */
@media (max-width: 768px) {
  .dashboard-page {
    overflow-x: hidden;
  }

  .topbar {
    height: 56px;
    padding: 0 16px;
    position: relative;
    justify-content: flex-end;
  }

  .brand {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 18px;
    white-space: nowrap;
  }

  .right {
    position: relative;
    z-index: 2;
  }

  .main {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }

  .left,
  .board {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .board {
    padding: 16px;
    overflow: hidden;
  }

  .board-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .table-wrap {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .table-wrap > div {
    width: max-content;
    min-width: 100%;
  }

  .modern-table {
    width: max-content;
    min-width: 560px;
    table-layout: auto;
  }

  .modern-table th,
  .modern-table td {
    font-size: 12px;
  }

  .modern-table th,
  .time {
    padding: 8px 6px !important;
  }

  .empty {
    height: 28px;
  }

  .session-text {
    padding: 6px;
  }

  .session-title {
    font-size: 12px;
  }

  .session-subtitle {
    font-size: 11px;
  }

  .modal-mask {
    padding: 12px;
    align-items: flex-start;
    overflow-y: auto;
  }

  .modal {
    width: 100%;
    max-width: 100%;
    margin-top: 16px;
    padding: 16px;
    border-radius: 18px;
  }

  .grid2 {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .modal-actions {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 8px;
    width: 100%;
  }

  .modal-actions .btn {
    width: 100% !important;
    display: block;
  }
}
</style>