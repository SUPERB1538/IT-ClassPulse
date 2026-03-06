from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from planner.models import Course, ClassSession


class AssignmentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u4", password="pass12345")
        self.course = Course.objects.create(user=self.user, course_name="C4", semester="S4")
        self.client.force_authenticate(user=self.user)

    def test_post_assignment_duplicate_title_returns_400(self):
        url = "/api/assignments/"
        due = (timezone.now() + timedelta(days=3)).isoformat()

        payload1 = {
            "course": self.course.id,
            "title": "Essay 1",
            "due_date": due,
            "status": "pending",
            "weighting": 0,
        }
        r1 = self.client.post(url, payload1, format="json")
        self.assertEqual(r1.status_code, 201, r1.data)

        # duplicate title (case-insensitive)
        payload2 = dict(payload1)
        payload2["title"] = "essay 1"
        r2 = self.client.post(url, payload2, format="json")
        self.assertEqual(r2.status_code, 400)
        self.assertIn("title", r2.data)


class SessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u5", password="pass12345")
        self.course = Course.objects.create(user=self.user, course_name="C5", semester="S5")
        self.client.force_authenticate(user=self.user)

        # existing session: Mon 10:00-11:00
        ClassSession.objects.create(
            course=self.course,
            day_of_week=1,
            start_time="10:00:00",
            end_time="11:00:00",
            location="Room A",
        )

    def test_post_session_overlap_returns_400(self):
        url = "/api/sessions/"
        payload = {
            "course": self.course.id,
            "day_of_week": 1,
            "start_time": "10:30:00",
            "end_time": "11:30:00",
            "location": "Room B",
        }
        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, 400)
        # 你的 viewset 抛的是 {"overlap": "..."}
        self.assertIn("overlap", r.data)