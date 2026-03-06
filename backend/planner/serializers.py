from rest_framework import serializers
from .models import Course, ClassSession, Assignment, StudyPlan
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal


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
    plan_days = serializers.CharField(write_only=True)
    plan_duration_human = serializers.CharField(read_only=True)
    plan_duration_seconds = serializers.IntegerField(read_only=True)

    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    course_name = serializers.CharField(source="assignment.course.course_name", read_only=True)
    time_left_seconds = serializers.SerializerMethodField()
    time_left_human = serializers.SerializerMethodField()
    assignment_status = serializers.CharField(source="assignment.status", read_only=True)

    class Meta:
        model = StudyPlan
        fields = [
            "id",
            "assignment",
            "assignment_title",
            "course_name",
            "assignment_status",
            "plan_days",            
            "plan_duration_seconds",  
            "plan_duration_human",     
            "created_at",
            "time_left_seconds",
            "time_left_human",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "plan_duration_seconds",
            "plan_duration_human",
            "time_left_seconds",
            "time_left_human",
        ]

    def _parse_ddhh_to_timedelta(self, value) -> timedelta:
        # Accept a compact "DD.HH" format such as 12.5 meaning 12 days 5 hours.
        # This keeps the form simple for users while still storing a proper duration.
        s = str(value).strip()
        if not s:
            raise serializers.ValidationError({"plan_days": "Enter duration like 12.5 meaning 12 days 5 hours."})

        if s.startswith("-"):
            raise serializers.ValidationError({"plan_days": "Duration cannot be negative."})

        if "." in s:
            d_str, h_str = s.split(".", 1)
            d_str = d_str or "0"
            h_str = (h_str[:2] if len(h_str) > 2 else h_str)

            if not d_str.isdigit() or not h_str.isdigit():
                raise serializers.ValidationError({"plan_days": "Use format DD.HH, e.g. 12.5 = 12 days 5 hours."})

            days = int(d_str)
            hours = int(h_str)
        else:
            if not s.isdigit():
                raise serializers.ValidationError({"plan_days": "Use format DD.HH, e.g. 12.5 = 12 days 5 hours."})
            days = int(s)
            hours = 0

        if hours < 0 or hours > 23:
            raise serializers.ValidationError({"plan_days": "Hours must be between 0 and 23 (e.g. 12.5 = 12d 5h)."})
        if days < 0:
            raise serializers.ValidationError({"plan_days": "Days cannot be negative."})

        return timedelta(days=days, hours=hours)

    def validate(self, attrs):
        # Study plans must fit within the time remaining before the assignment deadline.
        # This validation prevents users from creating impossible plans
        # such as a 5-day plan for work due tomorrow.
        assignment = attrs.get("assignment") or getattr(self.instance, "assignment", None)
        plan_days_input = attrs.get("plan_days", None)

        if assignment is None:
            return attrs
        
        if plan_days_input is None:
            duration = getattr(self.instance, "plan_duration", None)
            if duration is None:
                return attrs
        else:
            duration = self._parse_ddhh_to_timedelta(plan_days_input)

        due = assignment.due_date
        now = timezone.now()
        time_left_seconds = (due - now).total_seconds()

        if time_left_seconds <= 0:
            raise serializers.ValidationError({"plan_days": "Plan duration cannot exceed the remaining time before the assignment deadline."})

        plan_seconds = duration.total_seconds()

        if plan_seconds > time_left_seconds:
            d = int(time_left_seconds // 86400)
            h = int((time_left_seconds % 86400) // 3600)
            m = int((time_left_seconds % 3600) // 60)
            if d > 0:
                msg = f"Plan duration is too long. Only {d}d {h}h left before the deadline."
            elif h > 0:
                msg = f"Plan duration is too long. Only {h}h {m}m left before the deadline."
            else:
                msg = f"Plan duration is too long. Only {m}m left before the deadline."
            raise serializers.ValidationError({"plan_days": msg})

        attrs["plan_duration"] = duration
        attrs.pop("plan_days", None)
        return attrs

    def get_time_left_seconds(self, obj):
        due = obj.assignment.due_date
        now = timezone.now()
        return max(0, int((due - now).total_seconds()))

    def get_time_left_human(self, obj):
        secs = self.get_time_left_seconds(obj)
        if secs <= 0:
            return "Overdue"
        days = secs // 86400
        hours = (secs % 86400) // 3600
        minutes = (secs % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"