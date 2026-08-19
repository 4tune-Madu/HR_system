from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)


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