<template>
  <div class="page">
    <div class="topbar">
      <h2>Assignments</h2>
      <button class="btn" @click="goHome">← Home</button>
    </div>

    <!-- Filters -->
    <div class="card">
      <h3>Filters</h3>
      <div class="row">
        <input class="input" v-model="filters.q" placeholder="Search title / course..." />
        <select class="input" v-model="filters.status">
          <option value="">All</option>
          <option value="pending">pending</option>
          <option value="completed">completed</option>
        </select>
        <button class="btn ghost" @click="resetFilters">Reset</button>
        <button class="btn" @click="fetchAssignments">Search</button>
      </div>
    </div>

    <!-- Add assignment -->
    <div class="card">
      <h3>Add assignment</h3>

      <div class="row">
        <select class="input" v-model="createForm.course">
          <option value="">Select course</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.course_name }}</option>
        </select>

        <input class="input" v-model="createForm.title" placeholder="Title" />
        <input class="input" type="number" min="0" v-model.number="createForm.weighting" placeholder="Weighting" />
      </div>

      <div class="row">
        <input class="input" type="datetime-local" v-model="createForm.due_local" />
        <button class="btn" @click="createAssignment">Add</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- List -->
    <div class="card">
      <h3>Your assignments</h3>

      <div v-if="assignments.length === 0" class="empty">No assignments.</div>

      <div v-for="a in assignments" :key="a.id" class="item">
        <div class="item-left">
          <div class="titleline">
            <strong>{{ a.title }}</strong>

            <span class="badge ok" v-if="a.is_completed">completed</span>
            <span class="badge bad" v-else-if="a.is_overdue">overdue</span>
            <span class="badge warn" v-else>pending</span>
          </div>

          <div class="meta">
            due: {{ fmtDate(a.due_date) }} · weighting: {{ a.weighting }} ·
            course: {{ courseName(a.course) }}
          </div>
        </div>

        <div class="item-actions">
          <button
            class="btn ghost"
            v-if="!a.is_completed"
            @click="markCompleted(a.id)"
          >
            Mark completed
          </button>

          <button class="btn" @click="openEdit(a)">Edit</button>
          <button class="btn danger" @click="removeAssignment(a.id)">Delete</button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="editOpen" class="modal-mask" @click.self="closeEdit">
      <div class="modal">
        <div class="modal-header">
          <h3>Edit assignment</h3>
          <button class="iconbtn" @click="closeEdit">✕</button>
        </div>

        <div class="row">
          <select class="input" v-model="editForm.course">
            <option value="">Select course</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.course_name }}</option>
          </select>

          <input class="input" v-model="editForm.title" placeholder="Title" />
          <input class="input" type="number" min="0" v-model.number="editForm.weighting" />
        </div>

        <div class="row">
          <input class="input" type="datetime-local" v-model="editForm.due_local" />
        </div>

        <p v-if="editError" class="error">{{ editError }}</p>

        <div class="modal-actions">
          <button class="btn ghost" @click="closeEdit">Cancel</button>
          <button class="btn" @click="saveEdit">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "../api";

const router = useRouter();

const courses = ref([]);
const assignments = ref([]);

const error = ref("");

const filters = ref({
  q: "",
  status: "",
});

const createForm = ref({
  course: "",
  title: "",
  weighting: 10,
  due_local: "",
});

// ---------- edit modal ----------
const editOpen = ref(false);
const editError = ref("");
const editingId = ref(null);

const editForm = ref({
  course: "",
  title: "",
  weighting: 0,
  due_local: "",
});

// ---------- helpers ----------
function goHome() {
  router.push("/");
}

function resetFilters() {
  filters.value.q = "";
  filters.value.status = "";
  fetchAssignments();
}

function courseName(courseId) {
  const c = courses.value.find((x) => x.id === courseId);
  return c ? c.course_name : `#${courseId}`;
}

// ISO -> local string
function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString();
}

// datetime-local string -> ISO (UTC)
function localToISO(localStr) {
  // localStr: "2026-02-25T12:30"
  if (!localStr) return null;
  const dt = new Date(localStr);
  return dt.toISOString();
}

function isoToLocalInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  // datetime-local expects local time without seconds
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ---------- api ----------
async function fetchCourses() {
  const res = await api.get("/courses/");
  courses.value = res.data;
}

async function fetchAssignments() {
  error.value = "";
  const params = {};
  if (filters.value.q.trim()) params.q = filters.value.q.trim();
  if (filters.value.status.trim()) params.status = filters.value.status.trim();

  const res = await api.get("/assignments/", { params });
  assignments.value = res.data;
}

async function createAssignment() {
  error.value = "";
  try {
    if (!createForm.value.course) return (error.value = "Please select course");
    if (!createForm.value.title.trim()) return (error.value = "Title required");
    if (!createForm.value.due_local) return (error.value = "Due date required");

    await api.post("/assignments/", {
      course: createForm.value.course,
      title: createForm.value.title.trim(),
      weighting: createForm.value.weighting ?? 0,
      due_date: localToISO(createForm.value.due_local),
      status: "pending",
    });

    createForm.value.title = "";
    createForm.value.due_local = "";
    await fetchAssignments();
  } catch (e) {
    error.value = "Create failed";
  }
}

async function markCompleted(id) {
  await api.post(`/assignments/${id}/status/`, { status: "completed" });
  await fetchAssignments();
}

async function removeAssignment(id) {
  await api.delete(`/assignments/${id}/`);
  await fetchAssignments();
}

// ---------- edit ----------
function openEdit(a) {
  editError.value = "";
  editingId.value = a.id;

  editForm.value.course = a.course;
  editForm.value.title = a.title;
  editForm.value.weighting = a.weighting;
  editForm.value.due_local = isoToLocalInput(a.due_date);

  editOpen.value = true;
}

function closeEdit() {
  editOpen.value = false;
  editingId.value = null;
}

async function saveEdit() {
  editError.value = "";
  try {
    if (!editingId.value) return;

    if (!editForm.value.course) return (editError.value = "Please select course");
    if (!editForm.value.title.trim()) return (editError.value = "Title required");
    if (!editForm.value.due_local) return (editError.value = "Due date required");

    await api.patch(`/assignments/${editingId.value}/`, {
      course: editForm.value.course,
      title: editForm.value.title.trim(),
      weighting: editForm.value.weighting ?? 0,
      due_date: localToISO(editForm.value.due_local),
    });

    closeEdit();
    await fetchAssignments();
  } catch (e) {
    editError.value = "Save failed";
  }
}

onMounted(async () => {
  await fetchCourses();
  await fetchAssignments();
});
</script>

<style scoped>
.page {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.card {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 16px;
}
.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 10px;
  min-width: 220px;
}
.btn {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #111;
  color: #fff;
  cursor: pointer;
}
.btn.ghost {
  background: #f3f4f6;
  color: #111;
}
.btn.danger {
  background: #b91c1c;
}
.tip {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}
.error {
  margin-top: 8px;
  color: #b91c1c;
}
.empty {
  color: #666;
}
.item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 12px;
  margin-top: 10px;
}
.titleline {
  display: flex;
  align-items: center;
  gap: 10px;
}
.meta {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
}
.badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #eee;
}
.badge.ok {
  background: #ecfdf5;
}
.badge.warn {
  background: #fffbeb;
}
.badge.bad {
  background: #fef2f2;
}
.item-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

/* modal */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.35);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}
.modal {
  width: 720px;
  max-width: 100%;
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #eee;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.iconbtn {
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}
</style>