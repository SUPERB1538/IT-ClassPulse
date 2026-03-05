<template>
  <div class="page">
    <div class="topbar">
      <h2>Assignments</h2>
      <button class="btn" @click="goHome">← Home</button>
    </div>

    <!-- Add assignment -->
    <div class="card">
      <h3>Add assignment</h3>

      <div class="row">
        <select class="input" v-model="createForm.course">
          <option value="">Select course</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">
            {{ c.course_name }}
          </option>
        </select>

        <input
          class="input"
          v-model="createForm.title"
          placeholder="Title"
        />

        <input
          class="input"
          type="number"
          min="0"
          v-model.number="createForm.weighting"
          placeholder="Weighting"
        />
      </div>

      <div class="row">
        <input
          class="input"
          type="datetime-local"
          v-model="createForm.due_local"
        />

        <button class="btn" @click="createAssignment">
          Add
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- Assignments list -->
    <div class="card">

      <div class="row head-row">
        <h3 style="margin:0;">Your assignments</h3>

        <div class="search">
          <input
            class="input"
            v-model="filters.q"
            placeholder="Search title or course..."
            @keyup.enter="fetchAssignments"
          />

          <select class="input" v-model="filters.status">
            <option value="">All</option>
            <option value="pending">pending</option>
            <option value="completed">completed</option>
          </select>

          <button class="btn" @click="fetchAssignments">
            Search
          </button>

          <button
            class="btn ghost"
            @click="resetFilters"
            :disabled="!filters.q && !filters.status"
          >
            Clear
          </button>
        </div>
      </div>

      <div v-if="assignments.length === 0" class="empty">
        No assignments.
      </div>

      <div
        v-for="a in assignments"
        :key="a.id"
        class="assignment-card"
      >
        <div class="assignment-main">

          <div class="title-row">
            <div class="title">{{ a.title }}</div>

            <span
              class="badge ok"
              v-if="a.is_completed"
            >
              completed
            </span>

            <span
              class="badge bad"
              v-else-if="a.is_overdue"
            >
              overdue
            </span>

            <span
              class="badge warn"
              v-else
            >
              pending
            </span>
          </div>

          <div class="meta">
            Course: {{ courseName(a.course) }}
          </div>

          <div class="meta">
            Due: {{ fmtDate(a.due_date) }}
          </div>

          <div class="meta countdown">
            {{ deadlineText(a) }}
          </div>

          <!-- weighting progress -->
          <div class="progress-wrap">
            <div class="progress-label">
              Weight {{ a.weighting }}%
            </div>

            <div class="progress">
              <div
                class="bar"
                :style="{ width: Math.min(a.weighting,100) + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <div class="actions">
          <button
            class="btn ghost"
            v-if="!a.is_completed"
            @click="markCompleted(a.id)"
          >
            Complete
          </button>

          <button
            class="btn danger"
            @click="removeAssignment(a.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "../api"

const router = useRouter()

const courses = ref([])
const assignments = ref([])

const error = ref("")

const filters = ref({
  q: "",
  status: ""
})

const createForm = ref({
  course: "",
  title: "",
  weighting: 10,
  due_local: ""
})

function goHome(){
  router.push("/")
}

function resetFilters(){
  filters.value.q=""
  filters.value.status=""
  fetchAssignments()
}

function courseName(id){
  const c=courses.value.find(x=>x.id===id)
  return c ? c.course_name : `#${id}`
}

function fmtDate(iso){
  return new Date(iso).toLocaleString()
}

function localToISO(local){
  return new Date(local).toISOString()
}

function deadlineText(a){

  if(a.is_completed) return "Completed"

  const now=Date.now()
  const due=new Date(a.due_date).getTime()

  const diff=due-now

  if(diff<=0) return "Deadline passed"

  const d=Math.floor(diff/86400000)
  const h=Math.floor((diff%86400000)/3600000)

  if(d>0) return `${d} days ${h} hours left`
  return `${h} hours left`
}

async function fetchCourses(){
  const res=await api.get("/courses/")
  courses.value=res.data
}

async function fetchAssignments(){

  const params={}

  if(filters.value.q.trim())
    params.q=filters.value.q.trim()

  if(filters.value.status)
    params.status=filters.value.status

  const res=await api.get("/assignments/",{params})

  assignments.value=res.data
}

async function createAssignment(){

  error.value=""

  try{

    if(!createForm.value.course)
      return error.value="Select course"

    if(!createForm.value.title.trim())
      return error.value="Title required"

    await api.post("/assignments/",{
      course:createForm.value.course,
      title:createForm.value.title,
      weighting:createForm.value.weighting,
      due_date:localToISO(createForm.value.due_local),
      status:"pending"
    })

    createForm.value.title=""
    createForm.value.due_local=""

    fetchAssignments()

  }catch(e){
    error.value="Create failed"
  }
}

async function markCompleted(id){

  await api.post(`/assignments/${id}/status/`,{
    status:"completed"
  })

  fetchAssignments()
}

async function removeAssignment(id){

  if(!confirm("Delete assignment?")) return

  await api.delete(`/assignments/${id}/`)
  fetchAssignments()
}

onMounted(async()=>{
  await fetchCourses()
  await fetchAssignments()
})
</script>

<style scoped>

.page{
max-width:1100px;
margin:auto;
padding:24px;
}

.topbar{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:18px;
}

.card{
background:#fff;
border:1px solid #eee;
border-radius:14px;
padding:18px;
margin-bottom:20px;
}

.row{
display:flex;
gap:10px;
flex-wrap:wrap;
margin-top:10px;
}

.head-row{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:10px;
}

.search{
display:flex;
gap:10px;
flex-wrap:wrap;
}

.input{
padding:10px 12px;
border:1px solid #ddd;
border-radius:10px;
min-width:200px;
}

.btn{
padding:10px 14px;
border:none;
border-radius:10px;
background:#111;
color:#fff;
cursor:pointer;
}

.btn.ghost{
background:#f3f4f6;
color:#111;
}

.btn.danger{
background:#b91c1c;
}

.assignment-card{
display:flex;
justify-content:space-between;
gap:16px;
border:1px solid #eee;
border-radius:12px;
padding:16px;
margin-top:12px;
transition:.2s;
}

.assignment-card:hover{
box-shadow:0 4px 18px rgba(0,0,0,.06);
}

.title{
font-size:16px;
font-weight:600;
}

.title-row{
display:flex;
align-items:center;
gap:10px;
}

.meta{
font-size:13px;
color:#a32929;
margin-top:4px;
}

.countdown{
font-weight:500;
}

.badge{
font-size:12px;
padding:3px 10px;
border-radius:999px;
}

.badge.ok{
background:#ecfdf5;
}

.badge.warn{
background:#fffbeb;
}

.badge.bad{
background:#fef2f2;
}

.progress-wrap{
margin-top:10px;
}

.progress{
height:6px;
background:#eee;
border-radius:6px;
overflow:hidden;
margin-top:4px;
}

.bar{
height:100%;
background:#111;
}

.actions{
display:flex;
align-items:center;
gap:10px;
}

.empty{
color:#666;
}

.error{
color:#b91c1c;
margin-top:10px;
}

</style>