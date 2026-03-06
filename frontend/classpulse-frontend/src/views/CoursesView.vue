<template>
  <div class="page">

    <!-- top bar -->
    <div class="topbar">
      <h2>Courses</h2>
      <button class="btn" @click="router.push('/')">← Home</button>
    </div>

    <!-- add course -->
    <div class="card">
      <h3>Add course</h3>

      <div class="row">
        <input
          class="input"
          v-model="form.course_name"
          placeholder="Course name"
        />

        <input
          class="input"
          v-model="form.semester"
          placeholder="Semester (optional)"
        />

        <button
          class="btn add-btn"
          :disabled="loading"
          @click="createCourse"
        >
          {{ loading ? "Saving..." : "Add" }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- courses list -->
    <div class="card">

      <h3>Your courses</h3>

      <div v-if="loadingList">Loading...</div>

      <div v-else-if="courses.length === 0" class="muted">
        No courses yet.
      </div>

      <ul class="list">

        <li
          v-for="c in courses"
          :key="c.id"
          class="item"
        >

          <div class="left">
            <div class="title">{{ c.course_name }}</div>

            <div
              class="muted"
              v-if="c.semester"
            >
              {{ c.semester }}
            </div>
          </div>

          <div class="actions">

            <button
              class="btn ghost"
              @click="startEdit(c)"
            >
              Edit
            </button>

            <button
              class="btn danger"
              @click="removeCourse(c.id)"
            >
              Delete
            </button>

          </div>

        </li>

      </ul>
    </div>

    <!-- edit modal -->

    <div
      v-if="editing"
      class="modalMask"
      @click.self="editing=null"
    >

      <div class="modal">

        <h3>Edit course</h3>

        <input
          class="input"
          v-model="editing.course_name"
          placeholder="Course name"
        />

        <input
          class="input"
          v-model="editing.semester"
          placeholder="Semester"
        />

        <div class="modal-actions">
          <button
            class="btn ghost"
            @click="editing=null"
          >
            Cancel
          </button>

          <button
            class="btn"
            @click="saveEdit"
          >
            Save
          </button>
        </div>

        <p v-if="editError" class="error">
          {{ editError }}
        </p>

      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "../api"
import { ensureCsrf } from "../auth";

const router = useRouter()

const courses = ref([])
const loading = ref(false)
const loadingList = ref(false)
const error = ref("")

const form = ref({
  course_name: "",
  semester: ""
})

const editing = ref(null)
const editError = ref("")

async function fetchCourses(){

  loadingList.value = true

  try{
    const res = await api.get("/courses/")
    courses.value = res.data
  }
  finally{
    loadingList.value = false
  }

}

async function createCourse(){

  error.value = ""
  loading.value = true

  try{

    if(!form.value.course_name.trim())
      throw new Error("Course name required")

    await ensureCsrf()

    await api.post("/courses/",{
      course_name: form.value.course_name,
      semester: form.value.semester || ""
    })

    form.value = {
      course_name:"",
      semester:""
    }

    await fetchCourses()

  }catch(e){

    error.value =
      e?.response?.data
      ? JSON.stringify(e.response.data)
      : (e.message || String(e))

  }finally{
    loading.value=false
  }

}

function startEdit(c){
  editError.value=""
  editing.value={...c}
}

async function saveEdit(){

  editError.value=""

  try{

    await ensureCsrf()

    await api.put(`/courses/${editing.value.id}/`,{
      course_name: editing.value.course_name,
      semester: editing.value.semester || ""
    })

    editing.value=null

    await fetchCourses()

  }catch(e){

    editError.value =
      e?.response?.data
      ? JSON.stringify(e.response.data)
      : (e.message || String(e))

  }

}

async function removeCourse(id){

  if(!confirm("Delete this course?")) return

  await ensureCsrf()

  await api.delete(`/courses/${id}/`)

  await fetchCourses()

}

onMounted(fetchCourses)
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

.title{
  font-weight:600;
}

.muted{
  color:#6b7280;
  font-size:13px;
}

.actions{
  display:flex;
  gap:10px;
  align-items:center;
}

/* modal */

.modalMask{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,.3);
  display:flex;
  justify-content:center;
  align-items:center;
}

.modal{
  width:420px;
  background:white;
  border-radius:18px;
  padding:22px;
  box-shadow:0 20px 60px rgba(0,0,0,.18);
}

.modal-actions{
  display:flex;
  justify-content:flex-end;
  gap:10px;
  margin-top:12px;
}

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

  .row {
    flex-direction: column;
    align-items: stretch;
  }

  .add-btn {
    margin-left: 0;
  }

  .item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .left {
    min-width: 0;
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

  .modalMask {
    padding: 12px;
    align-items: flex-start;
    overflow-y: auto;
  }

  .modal {
    width: 100%;
    max-width: 100%;
    margin-top: 16px;
    padding: 16px;
  }

  .modal-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .modal-actions .btn {
    width: 100%;
  }
}
</style>