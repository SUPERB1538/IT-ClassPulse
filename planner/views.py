from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Assignment
from .models import Course
from django.shortcuts import redirect

@login_required
def dashboard(request):
    assignments = Assignment.objects.filter(course__user=request.user).order_by("due_date")
    return render(request, "dashboard.html", {"assignments": assignments})

@login_required
def course_list(request):
    courses = Course.objects.filter(user=request.user)
    return render(request, "course_list.html", {"courses": courses})

from django.shortcuts import redirect

@login_required
def add_course(request):
    if request.method == "POST":
        course_name = request.POST.get("course_name")
        semester = request.POST.get("semester")

        if course_name:
            Course.objects.create(
                user=request.user,
                course_name=course_name,
                semester=semester
            )
            return redirect("course_list")

    return render(request, "add_course.html")