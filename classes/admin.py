from django.contrib import admin

from .models import Class


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher_list", "student_list")
    search_fields = (
        "name",
        "teachers__username",
        "students__username",
    )
    filter_horizontal = ("teachers", "students")

    @admin.display(description="Teachers")
    def teacher_list(self, obj):
        return ", ".join(obj.teachers.values_list("username", flat=True))

    @admin.display(description="Students")
    def student_list(self, obj):
        return ", ".join(obj.students.values_list("username", flat=True))