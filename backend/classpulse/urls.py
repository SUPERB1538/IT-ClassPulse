from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from planner.api.viewsets import (
    CourseViewSet,
    ClassSessionViewSet,
    AssignmentViewSet,
    StudyPlanViewSet,
)
from planner.api.dashboard_views import dashboard_api
from planner.api.auth_views import (
    csrf,
    register,
    session_login,
    session_logout,
    me,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"sessions", ClassSessionViewSet, basename="sessions")
router.register(r"assignments", AssignmentViewSet, basename="assignments")
router.register(r"studyplans", StudyPlanViewSet, basename="studyplans")

urlpatterns = [
    path("admin/", admin.site.urls),

    # session auth
    path("api/auth/csrf/", csrf),
    path("api/auth/register/", register),
    path("api/auth/login/", session_login),
    path("api/auth/logout/", session_logout),
    path("api/auth/me/", me),

    # dashboard
    path("api/dashboard/", dashboard_api),

    # CRUD apis
    path("api/", include(router.urls)),
]