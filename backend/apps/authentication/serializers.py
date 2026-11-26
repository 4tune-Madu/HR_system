from django.contrib.auth import authenticate

from rest_framework import serializers
from apps.access.models import OrganizationMembership
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from django.contrib.auth.password_validation import (
    validate_password,
)
from drf_spectacular.utils import extend_schema_field

class LoginSerializer(
    TokenObtainPairSerializer
):
    username_field = "email"

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class TokenRefreshSerializer(
    serializers.Serializer
):
    refresh = serializers.CharField()


class MeSerializer(
    serializers.Serializer
):
    id = serializers.UUIDField(
        read_only=True
    )

    email = serializers.EmailField(
        read_only=True
    )

    first_name = serializers.CharField(
        read_only=True
    )

    last_name = serializers.CharField(
        read_only=True
    )

    is_active = serializers.BooleanField(
        read_only=True
    )

    is_staff = serializers.BooleanField(
        read_only=True
    )

    is_system_admin = serializers.BooleanField(
        source="is_superuser",
        read_only=True,
    )

    memberships = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    is_hr_admin = serializers.SerializerMethodField()
    is_payroll_admin = serializers.SerializerMethodField()

    def _role_codes(self, obj):
        return set(
            OrganizationMembership.objects
            .filter(user=obj, is_active=True)
            .values_list("role__code", flat=True)
        )

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_employee_id(self, obj):
        from apps.employee.models import Employee

        employee = Employee.objects.filter(
            user=obj,
            is_active=True,
        ).only('id').first()
        return employee.id if employee else None

    @extend_schema_field(serializers.BooleanField())
    def get_is_hr_admin(self, obj):
        return bool(self._role_codes(obj) & {"ORGANIZATION_ADMIN", "HR_MANAGER", "HR_OFFICER"})

    @extend_schema_field(serializers.BooleanField())
    def get_is_payroll_admin(self, obj):
        return "PAYROLL_ADMIN" in self._role_codes(obj)

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_memberships(self, obj):
        memberships = (
            OrganizationMembership.objects
            .filter(user=obj, is_active=True)
            .select_related("organization", "role")
            .prefetch_related("role__permissions")
        )
        return [
            {
                "organization_id": str(membership.organization_id),
                "organization_name": membership.organization.name,
                "role": membership.role.code,
                "permissions": list(
                    membership.role.permissions.values_list(
                        "code", flat=True
                    )
                ),
            }
            for membership in memberships
        ]


class SetPasswordSerializer(serializers.Serializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirmation = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):

        password = attrs["password"]
        password_confirmation = attrs[
            "password_confirmation"
        ]

        if password != password_confirmation:
            raise serializers.ValidationError(
                {
                    "password_confirmation": (
                        "Passwords do not match."
                    )
                }
            )

        validate_password(
            password,
            self.context.get("user"),
        )

        return attrs
