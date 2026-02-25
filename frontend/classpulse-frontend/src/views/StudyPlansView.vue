<template>
  <div class="page">
    <div class="top">
      <h2>Study Plans</h2>
      <button class="btn" @click="router.push('/')">← Home</button>
    </div>

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

        <button class="btn" :disabled="saving" @click="createPlan">
          {{ saving ? "Saving..." : "Add" }}
        </button>
      </div>

      <p v-if="addHint" class="muted">{{ addHint }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

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
          <button class="btn" @click="fetchPlans" :disabled="loading">Search</button>
          <button class="btn ghost" @click="clearSearch" :disabled="loading || !q">Clear</button>
        </div>
      </div>

      <div v-if="loading">Loading...</div>
      <div v-else-if="plans.length === 0" class="muted">No study plans.</div>

      <ul class="list">
        <li v-for="p in plans" :key="p.id" class="item">
          <div class="leftcol">
            <div class="title">
              {{ p.assignment_title }} ({{ p.course_name }})
              <span class="muted">
                · {{ p.plan_days }} day{{ p.plan_days === 1 ? "" : "s" }}
                <template v-if="p.time_left_human">
                  · Left: {{ p.time_left_human }}
                </template>
                <template v-else-if="typeof p.time_left_seconds === 'number'">
                  · Left: {{ formatSeconds(p.time_left_seconds) }}
                </template>
              </span>
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
            <button class="btn" v-if="editingId !== p.id" @click="startEdit(p)">
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
import { onMounted, ref, computed } from "vue";
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
  plan_days: 1,
});

// Edit state
const editingId = ref(null);
const editDays = ref(1);

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
  } finally {
    loading.value = false;
  }
}

function clearSearch() {
  q.value = "";
  fetchPlans();
}

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
  if (availableAssignments.value.length === 0) return "All assignments already have a study plan. Use Edit below.";
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

    await api.post("/studyplans/", {
      assignment: assignmentId,
      plan_days: Number(form.value.plan_days),
    });

    form.value.assignment = "";
    form.value.plan_days = 1;

    await fetchPlans();
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : (e.message || String(e));
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
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : (e.message || String(e));
  } finally {
    saving.value = false;
  }
}

async function removePlan(id) {
  if (!confirm("Delete this plan?")) return;
  await api.delete(`/studyplans/${id}/`);
  await fetchPlans();
}

onMounted(async () => {
  await fetchCourses();
  await fetchAssignments();
  await fetchPlans();
});
</script>

<style scoped>
.page { max-width: 980px; margin: 0 auto; padding: 24px; }
.top { display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px; }
.card { background:#fff; border:1px solid #eee; border-radius:14px; padding:16px; margin: 14px 0; }
.row { display:flex; gap:10px; flex-wrap:wrap; }
.head-row { align-items:center; justify-content:space-between; }
.search { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.input { padding:10px 12px; border:1px solid #ddd; border-radius:12px; min-width: 220px; flex: 1; }
.btn { padding:10px 12px; border-radius:12px; border:none; background:#111; color:#fff; cursor:pointer; }
.btn.danger { background:#b91c1c; }
.btn.ghost { background:#eee; color:#111; }
.list { list-style:none; padding:0; margin:12px 0 0; }
.item { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; padding:12px; border:1px solid #eee; border-radius:12px; margin-bottom:10px; }
.title { font-weight:600; }
.muted { color:#666; font-size:13px; }
.error { color:#b91c1c; margin-top:10px; font-size:13px; }

.leftcol { flex: 1; }
.actions { display:flex; gap:10px; align-items:center; }

.editrow { margin-top: 8px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.input.small { min-width: 120px; flex: 0; }
</style>