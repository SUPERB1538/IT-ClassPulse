<template>
  <div class="page dashboard-page">
    <!-- ===== Topbar ===== -->
    <header class="topbar">
      <div class="brand">ClassPulse</div>

      <div class="right">
        <div v-if="me" class="user-wrapper">
          <div class="avatar-container" @click.stop="toggleMenu">
            <div
              class="avatar"
              :style="{ backgroundColor: avatarColor }"
            >
              {{ userInitial }}
            </div>
            <div class="arrow" :class="{ open: menuOpen }"></div>
          </div>

          <div v-if="menuOpen" class="dropdown">
            <div class="dropdown-item" @click="go('/profile')">Profile</div>
            <div class="dropdown-item" @click="go('/settings')">Settings</div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item danger" @click="logoutNow">Logout</div>
          </div>
        </div>
      </div>
    </header>

    <!-- ===== Main Layout ===== -->
    <main class="main">
      <!-- Left Panel -->
      <section class="left">
        <div class="card" @click="go('/courses')">
          <div class="card-content">
            <div>
              <div class="card-title">Courses</div>
              <div class="card-sub">
                Browse and manage your courses.
              </div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card" @click="go('/assignments')">
          <div class="card-content">
            <div>
              <div class="card-title">Assignments</div>
              <div class="card-sub">
                Check deadlines and progress.
              </div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>

        <div class="card" @click="go('/studyplans')">
          <div class="card-content">
            <div>
              <div class="card-title">Study Plans</div>
              <div class="card-sub">
                Plan your study days before deadlines.
              </div>
            </div>
            <div class="card-action">View all</div>
          </div>
        </div>
      </section>

      <!-- Timetable -->
      <section class="board">
        <div class="board-header">
          <div class="board-title">Your Timetable</div>
          <a class="link" href="#" @click.prevent="onAddSession">
            + Add class session
          </a>
        </div>

        <div v-if="loading" class="pad muted">
          Loading timetable...
        </div>

        <div v-else-if="dashboard" class="table-wrap">
          <table class="modern-table">
            <thead>
              <tr>
                <th class="col-time">Time</th>
                <th v-for="d in dashboard.days" :key="d[0]">
                  {{ d[1] }}
                </th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="row in dashboard.rows" :key="row[0]">
                <td class="time">{{ row[0] }}</td>

                <template v-for="(cell, idx) in row[1]" :key="idx">
                  <td v-if="cell && cell.skip" style="display:none;"></td>
                  <td v-else-if="!cell" class="empty"></td>

                  <td
                    v-else
                    class="session"
                    :rowspan="cell.rowspan"
                  >
                    <div class="session-text">
                      {{ cell.text }}
                    </div>
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="pad muted">
          No timetable data.
        </div>
      </section>
    </main>
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
const menuOpen = ref(false);

/* ===== 首字母 ===== */
const userInitial = computed(() => {
  if (!me.value?.username) return "";
  return me.value.username.charAt(0).toUpperCase();
});

/* ===== 稳定随机颜色 ===== */
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

/* ===== 菜单控制 ===== */
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

function onAddSession() {
  alert("Add session modal");
}

onMounted(() => {
  loadAll();
  document.addEventListener("click", handleClickOutside);
});
</script>

<style scoped>

/* ===== Page ===== */
.dashboard-page {
  min-height: 100vh;
  background: #f5f5f7;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
               "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ===== Topbar ===== */
.topbar {
  height: 64px;
  padding: 0 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #e5e5e7;
}

.brand {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.3px;
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
  background: rgba(255,255,255,0.85);
  border-radius: 20px;
  padding: 22px;
  margin-bottom: 20px;
  box-shadow:
    0 2px 8px rgba(0,0,0,0.04),
    0 20px 40px rgba(0,0,0,0.06);
  transition: all 0.25s ease;
  cursor: pointer;
}

.left .card:hover {
  transform: translateY(-4px);
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
  align-self: flex-end;
  margin-top: 18px;
  font-size: 14px;
  font-weight: 500;
  padding: 6px 16px;
  border-radius: 20px;
  background: #f2f2f7;
  color: #0071e3;
  transition: all 0.2s ease;
}

.card-action:hover {
  background: #e5e5ea;
}

/* ===== Board ===== */
.board {
  background: rgba(255,255,255,0.9);
  border-radius: 24px;
  padding: 24px;
  box-shadow:
    0 2px 10px rgba(0,0,0,0.05),
    0 30px 80px rgba(0,0,0,0.06);
}

.board-title {
  font-size: 22px;
  font-weight: 600;
}

.modern-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.modern-table th {
  background: #f2f2f7;
  color: #6e6e73;
  font-weight: 500;
  padding: 12px;
}

.modern-table td {
  border: 1px solid #f2f2f7;
}

.time {
  font-weight: 500;
  color: #6e6e73;
  background: #fafafa;
}

.session {
  background: rgba(0,113,227,0.12);
  border-radius: 12px;
}

.session:hover {
  background: rgba(0,113,227,0.2);
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
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
  box-shadow: 0 12px 28px rgba(0,0,0,0.15);
  padding: 8px 0;
}

.dropdown-item {
  padding: 10px 16px;
  font-size: 14px;
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
</style>