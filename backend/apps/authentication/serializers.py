from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from django.contrib.auth.password_validation import (
    validate_password,
)

from apps.access.models import OrganizationMembership

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

    is_system_admin = serializers.SerializerMethodField()

    role_code = serializers.SerializerMethodField()

    is_hr_admin = serializers.SerializerMethodField()

    organization_id = serializers.SerializerMethodField()

    def _active_membership(self, user):
        return (
            OrganizationMembership.objects
            .select_related(
                "role",
                "organization",
            )
            .filter(
                user=user,
                is_active=True,
            )
            .order_by(
                "created_at"
            )
            .first()
        )

    def get_is_system_admin(self, obj):
        return bool(
            obj.is_superuser
            or obj.is_staff
            or self.get_role_code(obj) == "SYSTEM_ADMIN"
        )

    def get_role_code(self, obj):
        if obj.is_superuser or obj.is_staff:
            return "SYSTEM_ADMIN"

        membership = self._active_membership(obj)

        if membership is None:
            return "USER"

        return membership.role.code

    def get_is_hr_admin(self, obj):
        role_code = self.get_role_code(obj)
        return role_code in {
            "SYSTEM_ADMIN",
            "ORGANIZATION_ADMIN",
            "HR_MANAGER",
            "HR_OFFICER",
        }

    def get_organization_id(self, obj):
        membership = self._active_membership(obj)
        if membership is None:
            return None
        return str(membership.organization_id)


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