from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from planner.models import Course, Assignment
from planner.serializers import StudyPlanSerializer


class StudyPlanSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u3", password="pass12345")
        self.course = Course.objects.create(user=self.user, course_name="C3", semester="S3")
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="A",
            due_date=timezone.now() + timedelta(days=2),
            status="pending",
        )

    def test_parse_ddhh_valid(self):
        s = StudyPlanSerializer()
        self.assertEqual(s._parse_ddhh_to_timedelta("12.5"), timedelta(days=12, hours=5))
        self.assertEqual(s._parse_ddhh_to_timedelta("3"), timedelta(days=3))
        self.assertEqual(s._parse_ddhh_to_timedelta("0.23"), timedelta(hours=23))

    def test_parse_ddhh_invalid(self):
        s = StudyPlanSerializer()
        with self.assertRaises(ValidationError):
            s._parse_ddhh_to_timedelta("")
        with self.assertRaises(ValidationError):
            s._parse_ddhh_to_timedelta("-1")
        with self.assertRaises(ValidationError):
            s._parse_ddhh_to_timedelta("1.24")  # hours > 23
        with self.assertRaises(ValidationError):
            s._parse_ddhh_to_timedelta("abc")
        with self.assertRaises(ValidationError):
            s._parse_ddhh_to_timedelta("1.xx")

    def test_validate_rejects_duration_exceeds_deadline(self):
        # due in 2 days, but plan 3 days => error
        serializer = StudyPlanSerializer(data={
            "assignment": self.assignment.id,
            "plan_days": "3",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("plan_days", serializer.errors)

    def test_validate_accepts_and_sets_plan_duration(self):
        serializer = StudyPlanSerializer(data={
            "assignment": self.assignment.id,
            "plan_days": "1.5",  # 1 day 5 hours
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        validated = serializer.validated_data
        # plan_days to plan_duration，remove plan_days
        self.assertIn("plan_duration", validated)
        self.assertNotIn("plan_days", validated)
        self.assertEqual(validated["plan_duration"], timedelta(days=1, hours=5))