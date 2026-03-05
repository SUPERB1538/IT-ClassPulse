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
          v-model.number="form.plan_days"
          type="number"
          min="1"
          placeholder="Days"
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
      <div v-else-if="plans.length === 0" class="muted">No study plans.</div>

      <ul class="list" v-else>
        <li v-for="p in plans" :key="p.id" class="item">
          <div class="leftcol">
            <!-- 4-line info block (Assignments style) -->
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
                <span class="muted">({{ p.plan_days }} day{{ p.plan_days === 1 ? "" : "s" }})</span>
              </div>
            </div>

            <!-- Inline edit -->
            <div v-if="editingId === p.id" class="editrow">
              <input
                class="input small"
                type="number"
                min="1"
                v-model.number="editDays"
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

// Edit state
const editingId = ref(null);
const editDays = ref(1);

/** -----------------------------
 *  Countdown system (local)
 *  - Start time stored in localStorage per plan.id
 *  - UI updates every second
 * ------------------------------ */
const nowMs = ref(Date.now());
let timer = null;

const START_KEY = "studyplan_start_times_v1";
const startTimes = ref(loadStartTimes()); // { [planId]: ms }

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
  const total = Number(p.plan_days || 1) * 86400; // seconds
  const left = Math.floor((start + total * 1000 - nowMs.value) / 1000);
  return left;
}

function formatHMS(secs) {
  if (secs <= 0) return "Time up";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
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

    // Ensure each plan has a start time for countdown
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
const availableAssignments = computed(() =>
  assignments.value.filter((a) => !plannedAssignmentIds.value.has(a.id))
);

const addHint = computed(() => {
  if (!assignments.value.length) return "";
  if (availableAssignments.value.length === 0)
    return "All assignments already have a study plan. Use Edit below.";
  return "";
});

// backend due-time formatter
function formatSeconds(secs) {
  if (secs <= 0) return "Overdue";
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const mins = Math.floor((secs % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

// Line 3: Due text + class
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

// Line 4: Countdown text + class
function countdownText(p) {
  return formatHMS(planCountdownSeconds(p));
}

function countdownClass(p) {
  const left = planCountdownSeconds(p);
  if (left <= 0) return "bad";
  if (left <= 3600) return "warn"; // last hour
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
    if (!form.value.plan_days || form.value.plan_days < 1) throw new Error("Days must be >= 1");

    if (plans.value.some((p) => p.assignment === assignmentId)) {
      throw new Error("This assignment already has a study plan. Use Edit below.");
    }

    // create
    const res = await api.post("/studyplans/", {
      assignment: assignmentId,
      plan_days: Number(form.value.plan_days),
    });

    // if backend returns created plan with id, store start time immediately
    if (res?.data?.id) {
      startTimes.value[res.data.id] = Date.now();
      saveStartTimes();
    }

    form.value.assignment = "";
    form.value.plan_days = 1;

    await fetchPlans();
  } catch (e) {
    error.value = e?.response?.data
      ? JSON.stringify(e.response.data)
      : (e.message || String(e));
  } finally {
    saving.value = false;
  }
}

function startEdit(p) {
  error.value = "";
  editingId.value = p.id;
  editDays.value = Number(p.plan_days || 1);
}

function cancelEdit() {
  editingId.value = null;
  editDays.value = 1;
}

async function saveEdit(p) {
  error.value = "";
  saving.value = true;

  try {
    if (!editDays.value || editDays.value < 1) throw new Error("Days must be >= 1");

    await api.patch(`/studyplans/${p.id}/`, {
      plan_days: Number(editDays.value),
    });

    editingId.value = null;
    await fetchPlans();
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
  await api.delete(`/studyplans/${id}/`);

  // clean local countdown start time
  deleteStartTime(id);

  await fetchPlans();
}

/** -----------------------------
 *  Lifecycle
 * ------------------------------ */
onMounted(async () => {
  await fetchCourses();
  await fetchAssignments();
  await fetchPlans();

  timer = setInterval(() => {
    nowMs.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
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
</style>