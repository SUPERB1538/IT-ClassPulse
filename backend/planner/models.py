from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone


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

    def __str__(self):
        return self.title

    @property
    def is_completed(self):
        return self.status == "completed"

    @property
    def is_overdue(self):
        return (
            self.status != "completed"
            and self.due_date < timezone.now()
        )

    @property
    def is_pending(self):
        return (
            self.status != "completed"
            and self.due_date >= timezone.now()
        )


class StudyPlan(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="study_plans")
    plan_days = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.assignment.title} - {self.plan_days} days"
