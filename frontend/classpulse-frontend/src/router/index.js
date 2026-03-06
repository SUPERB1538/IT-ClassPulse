import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import { getMe } from "../auth";
import RegisterView from "../views/RegisterView.vue";
import CoursesView from "../views/CoursesView.vue";
import AssignmentsView from "../views/AssignmentsView.vue";
import StudyPlansView from "../views/StudyPlansView.vue";

const routes = [
  { path: "/login", name: "login", component: LoginView },
  { path: "/", name: "home", component: HomeView, meta: { requiresAuth: true } },
  { path: "/register", name: "register", component: RegisterView },
  { path: "/courses", name: "courses", component: CoursesView, meta: { requiresAuth: true } },
  { path: "/assignments", name: "assignments", component: AssignmentsView, meta: { requiresAuth: true } },
  { path: "/studyplans", name: "studyplans", component: StudyPlansView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

let cachedMe = null;

router.beforeEach(async (to) => {
  // Only protected routes need a session check.
  if (!to.meta.requiresAuth) return true;

  // Reuse the previous successful session lookup to avoid
  // calling /auth/me/ on every navigation within one session.
  if (cachedMe?.ok) return true;

  try {
    const me = await getMe();
    if (me?.ok) {
      cachedMe = me;
      return true;
    }
    // Preserve the target route so the user can be redirected back after login.
    return { path: "/login", query: { next: to.fullPath } };
  } catch {
    return { path: "/login", query: { next: to.fullPath } };
  }
});

export default router;