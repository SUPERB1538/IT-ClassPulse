from rest_framework import serializers
from .models import Course, ClassSession, Assignment, StudyPlan


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

    class Meta:
        model = StudyPlan
        fields = ["id", "assignment", "assignment_title", "plan_date", "plan_hours"]