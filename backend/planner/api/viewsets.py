from django.db.models import Q
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import Course, ClassSession, Assignment, StudyPlan
from ..serializers import CourseSerializer, ClassSessionSerializer, AssignmentSerializer, StudyPlanSerializer
from rest_framework.permissions import IsAuthenticated


# CRUD ViewSets
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Timetable sessions are scoped by course ownership and validated
# to avoid invalid time ranges or overlapping classes.
class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated]

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

    # Re-run the same ownership and overlap checks on edit,
    # excluding the current record from the conflict query.
    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")

        course = serializer.validated_data.get("course", instance.course)
        if course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")

        day = serializer.validated_data.get("day_of_week", instance.day_of_week)
        start = serializer.validated_data.get("start_time", instance.start_time)
        end = serializer.validated_data.get("end_time", instance.end_time)

        if start >= end:
            raise ValidationError({"time": "start_time must be earlier than end_time"})

        overlap = ClassSession.objects.filter(
            course__user=self.request.user,
            day_of_week=day
        ).exclude(id=instance.id).filter(
            Q(start_time__lt=end) & Q(end_time__gt=start)
        ).exists()

        if overlap:
            raise ValidationError({"overlap": "Time overlaps with an existing class session"})

        serializer.save()


# Supports CRUD plus lightweight search/filtering for dashboard use.
class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    # Allow searching by assignment title or course name from the frontend list view.
    def get_queryset(self):
        qs = (
            Assignment.objects
            .filter(course__user=self.request.user)
            .select_related("course")
            .order_by("due_date")
        )

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(course__course_name__icontains=q))

        status = (self.request.query_params.get("status") or "").strip()
        now = timezone.now()

        if status:
            if status == "overdue":
                qs = qs.filter(status="pending", due_date__lt=now)
            elif status == "pending":
                qs = qs.filter(status="pending", due_date__gte=now)
            elif status == "completed":
                qs = qs.filter(status="completed")
            else:
                qs = qs.none()

        return qs

    # Enforce case-insensitive uniqueness per course at the API layer as well,
    # so users get a clear validation message before hitting database constraints.
    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        if course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")

        title = (serializer.validated_data.get("title") or "").strip()
        if not title:
            raise ValidationError({"title": "title required"})

        if Assignment.objects.filter(course=course, title__iexact=title).exists():
            raise ValidationError({"title": "This title already exists in this course."})

        serializer.save(title=title)

    def perform_update(self, serializer):
        obj = serializer.instance
        course = obj.course

        if course.user_id != self.request.user.id:
            raise PermissionDenied("You don't own this course")

        title = serializer.validated_data.get("title", obj.title)
        title = (title or "").strip()
        if not title:
            raise ValidationError({"title": "title required"})

        if (
            Assignment.objects
            .filter(course=course, title__iexact=title)
            .exclude(id=obj.id)
            .exists()
        ):
            raise ValidationError({"title": "This title already exists in this course."})

        serializer.save(title=title)

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        a = self.get_object()
        status = (request.data.get("status") or "").strip()
        if status not in {"pending", "completed"}:
            raise ValidationError({"status": "Invalid status"})
        a.status = status
        a.save(update_fields=["status"])
        return Response({"ok": True, "id": a.id, "status": a.status})


# Study plans are limited to the current user's assignments
# and only one plan is allowed per assignment.
class StudyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = StudyPlanSerializer
    permission_classes = [IsAuthenticated]

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

    # Keep one study plan per assignment so countdown logic
    # and progress display stay simple and unambiguous in the UI.
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