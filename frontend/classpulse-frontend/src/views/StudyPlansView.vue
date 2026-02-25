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
          <option v-for="a in assignments" :key="a.id" :value="a.id">
            {{ a.title }} ({{ courseName(a.course) }})
          </option>
        </select>

        <input class="input" v-model="form.plan_date" type="date" />
        <input class="input" v-model.number="form.plan_hours" type="number" min="1" placeholder="Hours" />

        <button class="btn" :disabled="saving" @click="createPlan">
          {{ saving ? "Saving..." : "Add" }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div class="card">
      <h3>Your study plans</h3>

      <div v-if="loading">Loading...</div>
      <div v-else-if="plans.length === 0" class="muted">No study plans.</div>

      <ul class="list">
        <li v-for="p in plans" :key="p.id" class="item">
          <div>
            <div class="title">
              {{ assignmentTitle(p.assignment) }}
              <span class="muted">· {{ p.plan_date }} · {{ p.plan_hours }}h</span>
            </div>
          </div>

          <button class="btn danger" @click="removePlan(p.id)">Delete</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api";

const router = useRouter();

const courses = ref([]);
const assignments = ref([]);
const plans = ref([]);

const loading = ref(false);
const saving = ref(false);
const error = ref("");

const form = ref({
  assignment: "",
  plan_date: "",
  plan_hours: 1,
});

async function fetchCourses() {
  const res = await api.get("/courses/");
  courses.value = res.data;
}
async function fetchAssignments() {
  const res = await api.get("/assignments/");
  assignments.value = res.data;
}
async function fetchPlans() {
  loading.value = true;
  try {
    const res = await api.get("/studyplans/");
    plans.value = res.data;
  } finally {
    loading.value = false;
  }
}

function courseName(courseId) {
  const c = courses.value.find((x) => x.id === courseId);
  return c ? c.course_name : `#${courseId}`;
}
function assignmentTitle(assignmentId) {
  const a = assignments.value.find((x) => x.id === assignmentId);
  return a ? `${a.title} (${courseName(a.course)})` : `Assignment #${assignmentId}`;
}

async function createPlan() {
  error.value = "";
  saving.value = true;
  try {
    if (!form.value.assignment) throw new Error("Select an assignment");
    if (!form.value.plan_date) throw new Error("Select a date");
    if (!form.value.plan_hours || form.value.plan_hours < 1) throw new Error("Hours must be >= 1");

    await api.post("/studyplans/", {
      assignment: Number(form.value.assignment),
      plan_date: form.value.plan_date,
      plan_hours: Number(form.value.plan_hours),
    });

    form.value.assignment = "";
    form.value.plan_date = "";
    form.value.plan_hours = 1;

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
.input { padding:10px 12px; border:1px solid #ddd; border-radius:12px; min-width: 220px; flex: 1; }
.btn { padding:10px 12px; border-radius:12px; border:none; background:#111; color:#fff; cursor:pointer; }
.btn.danger { background:#b91c1c; }
.list { list-style:none; padding:0; margin:12px 0 0; }
.item { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px; border:1px solid #eee; border-radius:12px; margin-bottom:10px; }
.title { font-weight:600; }
.muted { color:#666; font-size:13px; }
.error { color:#b91c1c; margin-top:10px; font-size:13px; }
</style>