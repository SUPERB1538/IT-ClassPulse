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
  { path: "/courses", name: "courses", component: CoursesView },
  { path: "/assignments", name: "assignments", component: AssignmentsView },
  { path: "/studyplans", name: "studyplans", component: StudyPlansView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

let cachedMe = null;

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true;

  if (cachedMe?.ok) return true;

  try {
    const me = await getMe();
    if (me?.ok) {
      cachedMe = me;
      return true;
    }
    return { path: "/login", query: { next: to.fullPath } };
  } catch {
    return { path: "/login", query: { next: to.fullPath } };
  }
});

export default router;