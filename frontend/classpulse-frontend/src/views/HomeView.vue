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

        <!-- ✅ Study Plans card + preview list -->
        <div class="card" @click="go('/studyplans')">
          <div class="card-title">Study Plans</div>
          <div class="card-sub">Plan your study days before deadlines.</div>

          <!-- preview list -->
          <div class="plans-preview">
            <div v-if="plansLoading" class="muted small">Loading...</div>
            <div v-else-if="studyPlansPreview.length === 0" class="muted small">
              No study plans yet.
            </div>

            <ul v-else class="plans-list">
              <li v-for="p in studyPlansPreview" :key="p.id" class="plan-item">
                <div class="plan-main">
                  <span class="plan-title">
                    {{ p.assignment_title }} ({{ p.course_name }})
                  </span>
                </div>

                <div class="plan-meta">
                  {{ p.plan_days }} day{{ p.plan_days === 1 ? "" : "s" }}
                  · Left: {{ p.time_left_human || formatSeconds(p.time_left_seconds) }}
                </div>
              </li>

              <li v-if="studyPlans.length > studyPlansPreview.length" class="plan-more">
                View all ({{ studyPlans.length }}) →
              </li>
            </ul>
          </div>

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

    <!-- Add Class Session Modal -->
    <div v-if="showAddSession" class="modal-mask" @click.self="showAddSession=false">
      <div class="modal">
        <div class="modal-title">Add class session</div>

        <div class="form-row">
          <label>Course</label>
          <select v-model="sessionForm.course">
            <option v-for="c in courses" :key="c.id" :value="c.id">
              {{ c.course_name }}
            </option>
          </select>
        </div>

        <div class="form-row">
          <label>Day</label>
          <select v-model="sessionForm.day_of_week">
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
            <input type="time" v-model="sessionForm.start_time" />
          </div>
          <div class="form-row">
            <label>End</label>
            <input type="time" v-model="sessionForm.end_time" />
          </div>
        </div>

        <div class="form-row">
          <label>Location</label>
          <input v-model="sessionForm.location" placeholder="Optional" />
        </div>

        <div v-if="sessionError" class="error">{{ sessionError }}</div>

        <div class="actions">
          <button class="btn" @click="showAddSession=false">Cancel</button>
          <button class="btn primary" @click="addClassSession" :disabled="!sessionForm.course">
            Add
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
const error = ref("");

const courses = ref([]);
const showAddSession = ref(false);

const sessionForm = ref({
  course: "",
  day_of_week: 1,
  start_time: "09:00",
  end_time: "10:00",
  location: "",
});

const sessionError = ref("");

// Study plans preview data
const studyPlans = ref([]);
const plansLoading = ref(false);
const studyPlansPreview = computed(() => studyPlans.value.slice(0, 3));

function splitLines(text) {
  return String(text || "").split("\n");
}

function go(path) {
  router.push(path);
}

function formatSeconds(secs) {
  if (typeof secs !== "number") return "—";
  if (secs <= 0) return "Overdue";
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const mins = Math.floor((secs % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

async function loadStudyPlans() {
  plansLoading.value = true;
  try {
    const res = await api.get("/studyplans/");
    studyPlans.value = res.data || [];
  } catch (e) {
    studyPlans.value = [];
  } finally {
    plansLoading.value = false;
  }
}

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
    await ensureCsrf();

    const m = await getMe();
    if (!m?.ok) {
      router.replace("/login");
      return;
    }
    me.value = m;

    const res = await api.get("/dashboard/");
    dashboard.value = res.data;

    await loadStudyPlans();
  } catch (e) {
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

async function loadCourses() {
  const res = await api.get("/courses/");
  courses.value = res.data || [];
  if (!sessionForm.value.course && courses.value.length) {
    sessionForm.value.course = courses.value[0].id;
  }
}

async function addClassSession() {
  sessionError.value = "";
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

    const dashRes = await api.get("/dashboard/");
    dashboard.value = dashRes.data;
  } catch (e) {
    const data = e?.response?.data;
    sessionError.value = data
      ? (data.overlap || data.time || data.detail || JSON.stringify(data))
      : String(e);
  }
}

onMounted(async () => {
  await loadCourses();
  await loadAll();
});
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
.small {
  font-size: 12px;
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

/* study plans preview */
.plans-preview {
  margin-top: 10px;
}
.plans-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.plan-item {
  border-top: 1px solid #f0f0f0;
  padding: 10px 0;
}
.plan-title {
  font-weight: 600;
  font-size: 13px;
}
.plan-meta {
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}
.plan-more {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
  margin-top: 6px;
  color: #666;
  font-size: 12px;
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

/* modal */
.modal-mask{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.25);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.modal{
  width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,.15);
}
.modal-title{
  font-weight: 700;
  margin-bottom: 10px;
}
.form-row{
  display:flex;
  flex-direction:column;
  gap:6px;
  margin: 10px 0;
}
.form-row input, .form-row select{
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 0 10px;
}
.grid2{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.actions{
  display:flex;
  justify-content:flex-end;
  gap: 10px;
  margin-top: 12px;
}
.btn{
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background: #f5f5f5;
  cursor:pointer;
}
.btn.primary{
  background:#111;
  color:#fff;
  border-color:#111;
}
.btn:disabled{
  opacity: .5;
  cursor: not-allowed;
}
</style>