from django.contrib import admin
from .models import Course, Assignment, StudyPlan

admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(StudyPlan)
