import math
from datetime import time, datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.middleware.csrf import get_token
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.models import User

from .models import Course, ClassSession, Assignment, StudyPlan
from .serializers import CourseSerializer, ClassSessionSerializer, AssignmentSerializer, StudyPlanSerializer



@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    password2 = request.data.get("password2") or ""

    if not username:
        return Response({"ok": False, "error": "username required"}, status=400)
    if len(password) < 6:
        return Response({"ok": False, "error": "password too short (>=6)"}, status=400)
    if password != password2:
        return Response({"ok": False, "error": "passwords do not match"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "error": "username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)

    login(request, user)

    return Response({"ok": True, "username": user.username})



# Login for Session (Get CSRF)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def session_login(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"ok": False, "error": "Invalid username/password"}, status=400)
    login(request, user)
    return Response({"ok": True, "username": user.username})


@api_view(["POST"])
def session_logout(request):
    logout(request)
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "ok": True,
        "id": user.id,
        "username": user.username,
    })



# Dashboard grid
DAYS = [(1, "Mon"), (2, "Tue"), (3, "Wed"), (4, "Thu"), (5, "Fri"), (6, "Sat"), (7, "Sun")]


def _time_range(start: time, end: time, step_minutes: int = 30):
    dt = datetime.combine(datetime.today(), start)
    dt_end = datetime.combine(datetime.today(), end)
    step = timedelta(minutes=step_minutes)
    while dt < dt_end:
        yield dt.time()
        dt += step


def _fmt(t: time) -> str:
    return t.strftime("%H:%M")


@api_view(["GET"])
def dashboard_api(request):
    day_start = time(8, 0)
    day_end = time(19, 30)
    step = 30

    sessions = (
        ClassSession.objects.filter(course__user=request.user)
        .select_related("course")
        .order_by("day_of_week", "start_time")
    )

    slots = list(_time_range(day_start, day_end, step_minutes=step))
    slot_labels = [_fmt(t) for t in slots]
    grid = {label: {d: None for d, _ in DAYS} for label in slot_labels}

    for s in sessions:
        start_label = _fmt(s.start_time)
        start_dt = datetime.combine(datetime.today(), s.start_time)
        end_dt = datetime.combine(datetime.today(), s.end_time)
        minutes = int((end_dt - start_dt).total_seconds() // 60)
        span = max(1, math.ceil(minutes / step))

        text = s.course.course_name
        if s.location:
            text += f"\n{s.location}"

        if start_label in grid:
            grid[start_label][s.day_of_week] = {"text": text, "rowspan": span, "session_id": s.id}

            dt = start_dt + timedelta(minutes=step)
            for _ in range(span - 1):
                label = _fmt(dt.time())
                if label in grid:
                    grid[label][s.day_of_week] = {"skip": True}
                dt += timedelta(minutes=step)

    rows = []
    for label in slot_labels:
        row_cells = [grid[label][d] for d, _ in DAYS]
        rows.append([label, row_cells])

    return Response({"days": DAYS, "rows": rows})


# CRUD ViewSets
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        return Course.objects.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer

    def get_queryset(self):
        return (
            ClassSession.objects
            .filter(course__user=self.request.user)
            .select_related("course")
            .order_by("day_of_week", "start_time")
        )

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")

        day = serializer.validated_data["day_of_week"]
        start = serializer.validated_data["start_time"]
        end = serializer.validated_data["end_time"]

        if start >= end:
            raise ValidationError({"time": "start_time must be earlier than end_time"})

        overlap = ClassSession.objects.filter(
            course__user=self.request.user,
            day_of_week=day
        ).filter(
            Q(start_time__lt=end) & Q(end_time__gt=start)
        ).exists()

        if overlap:
            raise ValidationError({"overlap": "Time overlaps with an existing class session"})

        serializer.save()


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        qs = Assignment.objects.filter(course__user=self.request.user).select_related("course").order_by("due_date")

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(course__course_name__icontains=q))

        status = (self.request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)

        return qs

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")
        serializer.save()

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        a = self.get_object()
        status = (request.data.get("status") or "").strip()
        if status not in {"pending", "completed"}:
            raise ValidationError({"status": "Invalid status"})
        a.status = status
        a.save(update_fields=["status"])
        return Response({"ok": True, "id": a.id, "status": a.status})


class StudyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = StudyPlanSerializer

    def get_queryset(self):
        qs = (
            StudyPlan.objects.filter(assignment__course__user=self.request.user)
            .select_related("assignment", "assignment__course")
            .order_by("-created_at", "-id")
        )

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(assignment__title__icontains=q) |
                Q(assignment__course__course_name__icontains=q)
            )

        return qs

    def perform_create(self, serializer):
        assignment = serializer.validated_data["assignment"]
        if assignment.course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this assignment")

        if StudyPlan.objects.filter(assignment=assignment).exists():
            raise ValidationError({"assignment": "This assignment already has a study plan."})

        serializer.save()

    def perform_update(self, serializer):
        assignment = serializer.instance.assignment
        if assignment.course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this assignment")
        serializer.save()