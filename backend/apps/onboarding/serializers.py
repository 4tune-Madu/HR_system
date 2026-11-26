from django.utils import timezone
from rest_framework import serializers
from .models import OnboardingTask


class OnboardingTaskSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = OnboardingTask
        fields = ["id", "employee", "employee_name", "employee_number", "title", "status", "due_date", "notes", "completed_at", "created_at", "updated_at"]
        read_only_fields = ["id", "employee_name", "employee_number", "completed_at", "created_at", "updated_at"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Task title is required.")
        return value.strip()

    def update(self, instance, validated_data):
        status = validated_data.get("status")
        if status == OnboardingTask.Status.COMPLETED and instance.status != status:
            validated_data["completed_at"] = timezone.now()
        elif status and status != OnboardingTask.Status.COMPLETED:
            validated_data["completed_at"] = None
        return super().update(instance, validated_data)
