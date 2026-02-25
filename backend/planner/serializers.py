from rest_framework import serializers
from .models import Course, ClassSession, Assignment, StudyPlan
from datetime import timedelta
from django.utils import timezone


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "course_name", "semester"]


class ClassSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name", read_only=True)

    class Meta:
        model = ClassSession
        fields = ["id", "course", "course_name", "day_of_week", "start_time", "end_time", "location"]


class AssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name", read_only=True)

    is_completed = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "course_name",
            "title",
            "due_date",
            "status",
            "weighting",
            "is_completed",
            "is_overdue",
            "is_pending",
        ]


class StudyPlanSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    course_name = serializers.CharField(source="assignment.course.course_name", read_only=True)
    time_left_seconds = serializers.SerializerMethodField()
    time_left_human = serializers.SerializerMethodField()

    class Meta:
        model = StudyPlan
        fields = [
            "id",
            "assignment",
            "assignment_title", 
            "course_name", 
            "plan_days",
            "created_at",
            "time_left_seconds",
            "time_left_human",
        ]
        read_only_fields = ["id", "created_at", "time_left_seconds", "time_left_human"]

    def get_time_left_seconds(self, obj):
        due = obj.assignment.due_date
        now = timezone.now()
        delta = due - now
        return max(0, int(delta.total_seconds()))

    def get_time_left_human(self, obj):
        secs = self.get_time_left_seconds(obj)
        days = secs // 86400
        hours = (secs % 86400) // 3600
        minutes = (secs % 3600) // 60

        if secs <= 0:
            return "Overdue"
        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"