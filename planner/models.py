from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    course_name = models.CharField(max_length=200)
    semester = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.course_name} ({self.semester})" if self.semester else self.course_name


class Assignment(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    weighting = models.PositiveIntegerField(default=0)  # percentage 0-100

    def __str__(self):
        return self.title


class StudyPlan(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="study_plans")
    plan_date = models.DateField()
    plan_hours = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.assignment.title} - {self.plan_date} ({self.plan_hours}h)"
