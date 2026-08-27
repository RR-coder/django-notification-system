from django.conf import settings
from django.db import models


class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)

    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teaching_classes",
        blank=True,
    )

    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="enrolled_classes",
        blank=True,
    )

    def __str__(self):
        return self.name