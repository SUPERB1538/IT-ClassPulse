<template>
  <div class="page">
    <div class="topbar">
      <h2>Study Plans</h2>
      <button class="btn" @click="router.push('/')">← Home</button>
    </div>

    <!-- Add study plan -->
    <div class="card">
      <h3>Add study plan</h3>

      <div class="row">
        <select class="input" v-model="form.assignment">
          <option value="">Select assignment</option>
          <option v-for="a in availableAssignments" :key="a.id" :value="a.id">
            {{ a.title }} ({{ courseName(a.course) }})
          </option>
        </select>

        <input
          class="input"
          v-model="form.plan_days"
          type="text"
          inputmode="decimal"
          placeholder="DD.HH (e.g. 12.5 = 12d 5h)"
        />

        <button class="btn add-btn" :disabled="saving" @click="createPlan">
          {{ saving ? "Saving..." : "Add" }}
        </button>
      </div>

      <p v-if="addHint" class="muted">{{ addHint }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- Plans list -->
    <div class="card">
      <div class="row head-row">
        <h3 style="margin:0;">Your study plans</h3>

        <div class="search">
          <input
            class="input"
            v-model="q"
            placeholder="Search by assignment or course..."
            @keyup.enter="fetchPlans"
          />
          <button class="btn ghost" @click="clearSearch" :disabled="loading || !q">
            Clear
          </button>
          <button class="btn" @click="fetchPlans" :disabled="loading">
            Search
          </button>
        </div>
      </div>

      <div v-if="loading">Loading...</div>
      <div v-else-if="visiblePlans.length === 0" class="muted">No study plans.</div>

      <ul class="list" v-else>
        <li v-for="p in visiblePlans" :key="p.id" class="item">
          <div class="leftcol">
            <div class="info">
              <div class="line1">{{ p.assignment_title }}</div>

              <div class="line2 muted">Course: {{ p.course_name }}</div>

              <div class="line3">
                <span class="muted">Due:</span>
                <span :class="['due', dueClass(p)]">
                  {{ dueText(p) }}
                </span>
              </div>

              <div class="line4">
                <span class="muted">Plan countdown:</span>
                <span :class="['countdown', countdownClass(p)]">
                  {{ countdownText(p) }}
                </span>
                <span class="muted">({{ p.plan_duration_human }})</span>
              </div>
            </div>

            <!-- Inline edit -->
            <div v-if="editingId === p.id" class="editrow">
              <input
                class="input small"
                type="text"
                inputmode="decimal"
                v-model="editDays"
              />
              <button class="btn" :disabled="saving" @click="saveEdit(p)">
                {{ saving ? "Saving..." : "Save" }}
              </button>
              <button class="btn ghost" :disabled="saving" @click="cancelEdit">
                Cancel
              </button>
            </div>
          </div>

          <div class="actions">
            <button class="btn ghost" v-if="editingId !== p.id" @click="startEdit(p)">
              Edit
            </button>
            <button class="btn danger" @click="removePlan(p.id)">
              Delete
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { ensureCsrf } from "../auth";
import api from "../api";

const router = useRouter();

const courses = ref([]);
const assignments = ref([]);
const plans = ref([]);

const loading = ref(false);
const saving = ref(false);
const error = ref("");

const q = ref("");

const form = ref({
  assignment: "",
  plan_days: null,
});

const editingId = ref(null);
const editDays = ref(1);

// Convert stored duration seconds back into the compact DD.HH input format
// so inline editing stays consistent with the create form.
function secondsToDayHour(seconds) {
  const secs = Number(seconds || 0);
  const d = Math.floor(secs / 86400);
  const h = Math.floor((secs % 86400) / 3600);
  return `${d}.${h}`; 
}

/** -----------------------------
 *  Countdown system 
 * ------------------------------ */
const nowMs = ref(Date.now());
let timer = null;

// Keep countdown start times in localStorage so timers do not reset after refresh.
const START_KEY = "studyplan_start_times_v1";
const startTimes = ref(loadStartTimes()); 

function loadStartTimes() {
  try {
    return JSON.parse(localStorage.getItem(START_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveStartTimes() {
  localStorage.setItem(START_KEY, JSON.stringify(startTimes.value));
}

function ensureStartTime(planId) {
  if (!planId) return Date.now();
  if (!startTimes.value[planId]) {
    startTimes.value[planId] = Date.now();
    saveStartTimes();
  }
  return startTimes.value[planId];
}

function deleteStartTime(planId) {
  if (!planId) return;
  if (startTimes.value[planId]) {
    delete startTimes.value[planId];
    saveStartTimes();
  }
}

function planCountdownSeconds(p) {
  const start = ensureStartTime(p.id);
  const total = Number(p.plan_duration_seconds || 86400);
  const left = Math.floor((start + total * 1000 - nowMs.value) / 1000);
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

/** -----------------------------
 *  Data fetching
 * ------------------------------ */
async function fetchCourses() {
  const res = await api.get("/courses/");
  courses.value = res.data || [];
}

async function fetchAssignments() {
  const res = await api.get("/assignments/");
  assignments.value = res.data || [];
}

async function fetchPlans() {
  loading.value = true;
  try {
    const params = {};
    if (q.value.trim()) params.q = q.value.trim();
    const res = await api.get("/studyplans/", { params });
    plans.value = res.data || [];

    plans.value.forEach((p) => ensureStartTime(p.id));
  } finally {
    loading.value = false;
  }
}

function clearSearch() {
  q.value = "";
  fetchPlans();
}

/** -----------------------------
 *  Helpers
 * ------------------------------ */
function courseName(courseId) {
  const c = courses.value.find((x) => x.id === courseId);
  return c ? c.course_name : `#${courseId}`;
}

const plannedAssignmentIds = computed(() => new Set(plans.value.map((p) => p.assignment)));
const availableAssignments = computed(() => {
  // Only assignments that are still active and do not already have a plan
  // should appear in the "Add study plan" dropdown.
  return assignments.value.filter((a) => {
    if (plannedAssignmentIds.value.has(a.id)) return false;

    const status = (a.status || a.state || "").toString().toLowerCase();
    const isCompleted =
      a.completed === true ||
      a.is_completed === true ||
      status === "completed" ||
      status === "done";

    if (isCompleted) return false;

    if (typeof a.time_left_seconds === "number" && a.time_left_seconds <= 0) return false;
    if (typeof a.time_left_human === "string" && a.time_left_human.toLowerCase().includes("overdue"))
      return false;

    const dueStr = a.due_date || a.due || a.deadline;
    if (dueStr) {
      const dueMs = Date.parse(dueStr);
      if (!Number.isNaN(dueMs) && dueMs <= Date.now()) return false;
    }

    return true;
  });
});

const eligibleAssignmentIds = computed(() => {
  const ok = new Set();

  for (const a of assignments.value) {
    const status = (a.status || a.state || "").toString().toLowerCase();

    const isCompleted =
      a.completed === true ||
      a.is_completed === true ||
      status === "completed" ||
      status === "done";

    if (isCompleted) continue;

    if (typeof a.time_left_seconds === "number" && a.time_left_seconds <= 0) continue;
    if (
      typeof a.time_left_human === "string" &&
      a.time_left_human.toLowerCase().includes("overdue")
    ) continue;

    const dueStr = a.due_date || a.due || a.deadline;
    if (dueStr) {
      const dueMs = Date.parse(dueStr);
      if (!Number.isNaN(dueMs) && dueMs <= Date.now()) continue;
    }

    ok.add(a.id);
  }

  return ok;
});

const visiblePlans = computed(() =>
  plans.value.filter((p) => eligibleAssignmentIds.value.has(p.assignment))
);

const addHint = computed(() => {
  if (!assignments.value.length) return "";
  if (availableAssignments.value.length === 0)
    return "No eligible assignments. Only pending (not overdue, not completed) assignments can be added.";
  return "";
});

function formatSeconds(secs) {
  if (secs <= 0) return "Overdue";
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const mins = Math.floor((secs % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

function dueText(p) {
  if (p.time_left_human) return p.time_left_human;
  if (typeof p.time_left_seconds === "number") return formatSeconds(p.time_left_seconds);
  return "N/A";
}

function dueClass(p) {
  const secs = p.time_left_seconds;
  if (typeof secs === "number" && secs <= 0) return "bad";
  return "ok";
}

function countdownText(p) {
  return formatHMS(planCountdownSeconds(p));
}

function countdownClass(p) {
  const left = planCountdownSeconds(p);
  if (left <= 0) return "bad";
  if (left <= 3600) return "warn"; 
  return "ok";
}

/** -----------------------------
 *  CRUD
 * ------------------------------ */
async function createPlan() {
  error.value = "";
  saving.value = true;

  try {
    const assignmentId = Number(form.value.assignment);

    if (!assignmentId) throw new Error("Select an assignment");
    const v = String(form.value.plan_days || "").trim();
    if (!v) throw new Error("Enter duration like 12.5 (12d 5h)");

    if (plans.value.some((p) => p.assignment === assignmentId)) {
      throw new Error("This assignment already has a study plan. Use Edit below.");
    }

    await ensureCsrf();

    const res = await api.post("/studyplans/", {
      assignment: assignmentId,
      plan_days: String(form.value.plan_days).trim(),
    });

    if (res?.data?.id) {
      startTimes.value[res.data.id] = Date.now();
      saveStartTimes();
    }

    form.value.assignment = "";
    form.value.plan_days = 1;

    await fetchPlans();
    window.dispatchEvent(new Event("studyplans:changed"));
  } catch (e) {
    error.value =
      e?.response?.data?.plan_days?.[0] ||
      e?.response?.data?.detail ||
      e.message ||
      "Failed to create study plan";
  } finally {
    saving.value = false;
  }
}

function startEdit(p) {
  error.value = "";
  editingId.value = p.id;
  editDays.value = secondsToDayHour(p.plan_duration_seconds);
}

function cancelEdit() {
  editingId.value = null;
  editDays.value = 1;
}

async function saveEdit(p) {
  error.value = "";
  saving.value = true;

  try {
    const v = String(editDays.value || "").trim();
    if (!v) throw new Error("Enter duration like 12.5 (12d 5h)");

    await ensureCsrf();

    await api.patch(`/studyplans/${p.id}/`, {
      plan_days: String(editDays.value).trim(),
    });

    editingId.value = null;
    await fetchPlans();
    window.dispatchEvent(new Event("studyplans:changed"));
  } catch (e) {
    error.value = e?.response?.data
      ? JSON.stringify(e.response.data)
      : (e.message || String(e));
  } finally {
    saving.value = false;
  }
}

async function removePlan(id) {
  if (!confirm("Delete this plan?")) return;

  await ensureCsrf();

  await api.delete(`/studyplans/${id}/`);

  deleteStartTime(id);

  await fetchPlans();
  window.dispatchEvent(new Event("studyplans:changed"));
}

/** -----------------------------
 *  Lifecycle
 * ------------------------------ */
async function refreshAll() {
  await fetchAssignments();
  await fetchPlans();
}

onMounted(async () => {
  await fetchCourses();
  await refreshAll();

  timer = setInterval(() => {
    nowMs.value = Date.now();
  }, 1000);

  window.addEventListener("focus", refreshAll);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
  window.removeEventListener("focus", refreshAll);
});
</script>

<style scoped>
.page{
  max-width:1100px;
  margin:auto;
  padding:40px 24px;
}

/* topbar */
.topbar{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:26px;
}

.topbar h2{
  font-size:26px;
  font-weight:700;
}

/* cards */
.card{
  background:white;
  border-radius:18px;
  padding:22px;
  margin-bottom:20px;
  border:1px solid #f1f1f1;
  box-shadow:0 10px 30px rgba(0,0,0,.05);
}

.card h3{
  margin-bottom:14px;
}

/* layout */
.row{
  display:flex;
  gap:12px;
  align-items:center;
  flex-wrap:wrap;
}

.head-row{
  justify-content:space-between;
}

/* search block */
.search{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
}

/* inputs */
.input{
  padding:12px 14px;
  border:1px solid #e5e7eb;
  border-radius:14px;
  min-width:220px;
  font-size:14px;
  transition:.2s;
}

.input:focus{
  outline:none;
  border-color:#4f46e5;
  box-shadow:0 0 0 3px rgba(79,70,229,.15);
}

/* buttons */
.btn{
  padding:10px 16px;
  border:none;
  border-radius:12px;
  background:#111827;
  color:white;
  cursor:pointer;
  transition:.2s;
}

.btn:hover{
  transform:translateY(-1px);
  box-shadow:0 6px 18px rgba(0,0,0,.15);
}

.btn:disabled{
  opacity:.6;
  cursor:not-allowed;
  transform:none;
  box-shadow:none;
}

.btn.ghost{
  background:#d9dfe2;
  color:#111;
}

.btn.danger{
  background:#dc2626;
}

.add-btn{
  margin-left:auto;
}

/* list */
.list{
  list-style:none;
  padding:0;
  margin-top:16px;
}

.item{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:12px;
  padding:16px;
  border-radius:14px;
  border:1px solid #eee;
  margin-bottom:12px;
  transition:.2s;
  background:#f8fafc;
}

.item:hover{
  background:#fafafa;
  transform:translateY(-2px);
  box-shadow:0 10px 30px rgba(0,0,0,.06);
}

.leftcol{
  flex:1;
  min-width:260px;
}

/* 4-line info block */
.info{
  display:flex;
  flex-direction:column;
  gap:6px;
}

.line1{
  font-weight:700;
  font-size:15px;
  color:#111827;
}

.line3, .line4{
  font-size:13px;
  display:flex;
  gap:8px;
  align-items:center;
  flex-wrap:wrap;
}

.muted{
  color:#6b7280;
  font-size:13px;
}

/* due & countdown colors */
.due.ok, .countdown.ok{
  color:#111827;
}

.due.bad{
  color:#dc2626;
  font-weight:600;
}

.countdown.warn{
  color:#b45309;
  font-weight:700;
}

.countdown.bad{
  color:#dc2626;
  font-weight:800;
}

/* actions */
.actions{
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
}

/* inline edit row */
.editrow{
  margin-top:10px;
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
}

.input.small{
  min-width:120px;
  flex:0;
}

/* error */
.error{
  color:#dc2626;
  margin-top:10px;
  font-size:13px;
}

@media (max-width: 768px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .head-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .search {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .assignment-card {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .assignment-main {
    min-width: 0;
  }

  .title-row {
    flex-wrap: wrap;
  }

  .actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .actions .btn {
    width: 100%;
  }

  .edit-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .add-btn {
    margin-left: 0;
  }
}
</style>