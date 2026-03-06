from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from planner.models import Course, Assignment, StudyPlan


class AssignmentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.course = Course.objects.create(user=self.user, course_name="C1", semester="S1")

    def test_assignment_flags_pending_future_due(self):
        a = Assignment.objects.create(
            course=self.course,
            title="A1",
            due_date=timezone.now() + timedelta(days=1),
            status="pending",
        )
        self.assertFalse(a.is_completed)
        self.assertFalse(a.is_overdue)
        self.assertTrue(a.is_pending)

    def test_assignment_flags_pending_past_due(self):
        a = Assignment.objects.create(
            course=self.course,
            title="A2",
            due_date=timezone.now() - timedelta(minutes=1),
            status="pending",
        )
        self.assertFalse(a.is_completed)
        self.assertTrue(a.is_overdue)
        self.assertFalse(a.is_pending)

    def test_assignment_flags_completed(self):
        a = Assignment.objects.create(
            course=self.course,
            title="A3",
            due_date=timezone.now() - timedelta(days=10),
            status="completed",
        )
        self.assertTrue(a.is_completed)
        self.assertFalse(a.is_overdue)
        self.assertFalse(a.is_pending)


class StudyPlanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="pass12345")
        self.course = Course.objects.create(user=self.user, course_name="C2", semester="S2")
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="A",
            due_date=timezone.now() + timedelta(days=7),
            status="pending",
        )

    def test_plan_duration_human(self):
        sp = StudyPlan.objects.create(
            assignment=self.assignment,
            plan_duration=timedelta(days=2, hours=5),
        )
        self.assertEqual(sp.plan_duration_seconds, 2 * 86400 + 5 * 3600)
        self.assertEqual(sp.plan_duration_human, "2d 5h")

    def test_plan_duration_seconds_never_negative(self):
        sp = StudyPlan.objects.create(
            assignment=self.assignment,
            plan_duration=timedelta(days=-1),
        )
        self.assertEqual(sp.plan_duration_seconds, 0)