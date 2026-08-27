from rest_framework import generics

from accounts.permissions import IsAdmin

from .models import Class
from .serializers import ClassSerializer


class ClassListCreateView(generics.ListCreateAPIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdmin]


class ClassDetailView(generics.RetrieveUpdateAPIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdmin]