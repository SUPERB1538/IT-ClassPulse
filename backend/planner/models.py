from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    course_name = models.CharField(max_length=200)
    semester = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.course_name} ({self.semester})" if self.semester else self.course_name


class ClassSession(models.Model):
    DAYS = [
        (1, "Mon"),
        (2, "Tue"),
        (3, "Wed"),
        (4, "Thu"),
        (5, "Fri"),
        (6, "Sat"),
        (7, "Sun"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.course.course_name} {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


# Assignments are unique per course title so the same course
# cannot accidentally contain duplicate entries for one task.
class Assignment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    weighting = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "title"], name="uniq_assignment_title_per_course")
        ]

    def __str__(self):
        return self.title
    
    @property
    def is_completed(self):   
        # Convenience flags are exposed to the frontend so UI logic
        # does not need to re-implement status checks everywhere.
        return self.status == "completed"

    @property
    def is_overdue(self):
        # An assignment is overdue only if it has passed its deadline
        # and has not already been marked as completed.
        return self.status != "completed" and self.due_date < timezone.now()

    @property
    def is_pending(self):
        # "Pending" here means still active: not completed and not past due.
        return self.status != "completed" and self.due_date >= timezone.now()


class StudyPlan(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="study_plans")
    plan_duration = models.DurationField()
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def plan_duration_seconds(self):
        # Normalise duration for countdown display and API responses.
        return max(0, int(self.plan_duration.total_seconds())) if self.plan_duration else 0

    @property
    def plan_duration_human(self):
        # Keep a compact human-readable version for the frontend
        # so the UI does not need to format raw duration values.
        secs = self.plan_duration_seconds
        d = secs // 86400
        h = (secs % 86400) // 3600
        return f"{d}d {h}h"

    def __str__(self):
        return f"{self.assignment.title} - {self.plan_duration_human}"
