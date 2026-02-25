<template>
  <div class="page">
    <div class="top">
      <h2>Courses</h2>
      <button class="btn" @click="router.push('/')">← Home</button>
    </div>

    <div class="card">
      <h3>Add course</h3>
      <div class="row">
        <input class="input" v-model="form.course_name" placeholder="Course name" />
        <input class="input" v-model="form.semester" placeholder="Semester (optional)" />
        <button class="btn" :disabled="loading" @click="createCourse">
          {{ loading ? "Saving..." : "Add" }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div class="card">
      <h3>Your courses</h3>

      <div v-if="loadingList">Loading...</div>
      <div v-else-if="courses.length === 0" class="muted">No courses yet.</div>

      <ul class="list">
        <li v-for="c in courses" :key="c.id" class="item">
          <div>
            <div class="title">{{ c.course_name }}</div>
            <div class="muted" v-if="c.semester">{{ c.semester }}</div>
          </div>

          <div class="actions">
            <button class="btn ghost" @click="startEdit(c)">Edit</button>
            <button class="btn danger" @click="removeCourse(c.id)">Delete</button>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="editing" class="modalMask" @click.self="editing=null">
      <div class="modal">
        <h3>Edit course</h3>
        <input class="input" v-model="editing.course_name" placeholder="Course name" />
        <input class="input" v-model="editing.semester" placeholder="Semester (optional)" />
        <div class="actions">
          <button class="btn ghost" @click="editing=null">Cancel</button>
          <button class="btn" @click="saveEdit">Save</button>
        </div>
        <p v-if="editError" class="error">{{ editError }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api";

const router = useRouter();

const courses = ref([]);
const loading = ref(false);
const loadingList = ref(false);
const error = ref("");

const form = ref({ course_name: "", semester: "" });

const editing = ref(null);
const editError = ref("");

async function fetchCourses() {
  loadingList.value = true;
  try {
    const res = await api.get("/courses/");
    courses.value = res.data;
  } finally {
    loadingList.value = false;
  }
}

async function createCourse() {
  error.value = "";
  loading.value = true;
  try {
    if (!form.value.course_name.trim()) throw new Error("Course name required");
    await api.post("/courses/", {
      course_name: form.value.course_name,
      semester: form.value.semester || "",
    });
    form.value = { course_name: "", semester: "" };
    await fetchCourses();
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : (e.message || String(e));
  } finally {
    loading.value = false;
  }
}

function startEdit(c) {
  editError.value = "";
  editing.value = { ...c };
}

async function saveEdit() {
  editError.value = "";
  try {
    const c = editing.value;
    await api.put(`/courses/${c.id}/`, {
      course_name: c.course_name,
      semester: c.semester || "",
    });
    editing.value = null;
    await fetchCourses();
  } catch (e) {
    editError.value = e?.response?.data ? JSON.stringify(e.response.data) : (e.message || String(e));
  }
}

async function removeCourse(id) {
  if (!confirm("Delete this course?")) return;
  await api.delete(`/courses/${id}/`);
  await fetchCourses();
}

onMounted(fetchCourses);
</script>

<style scoped>
.page { max-width: 980px; margin: 0 auto; padding: 24px; }
.top { display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px; }
.card { background:#fff; border:1px solid #eee; border-radius:14px; padding:16px; margin: 14px 0; }
.row { display:flex; gap:10px; flex-wrap:wrap; }
.input { padding:10px 12px; border:1px solid #ddd; border-radius:12px; min-width: 220px; flex: 1; }
.btn { padding:10px 12px; border-radius:12px; border:none; background:#111; color:#fff; cursor:pointer; }
.btn.ghost { background:#f3f4f6; color:#111; border:1px solid #e5e7eb; }
.btn.danger { background:#b91c1c; }
.list { list-style:none; padding:0; margin:12px 0 0; }
.item { display:flex; justify-content:space-between; align-items:center; padding:12px; border:1px solid #eee; border-radius:12px; margin-bottom:10px; }
.title { font-weight:600; }
.muted { color:#666; font-size:13px; }
.error { color:#b91c1c; margin-top:10px; font-size:13px; }

.modalMask { position:fixed; inset:0; background:rgba(0,0,0,.25); display:grid; place-items:center; }
.modal { width:420px; background:#fff; border-radius:14px; padding:16px; border:1px solid #eee; }
.actions { display:flex; justify-content:flex-end; gap:10px; margin-top:12px; }
</style>