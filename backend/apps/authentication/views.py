from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    MeSerializer,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)

from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


class LoginView(APIView):

    permission_classes = [
        AllowAny
    ]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
        },
        tags=["Authentication"],
    )
    def post(self, request):

        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):

    @extend_schema(
        request=inline_serializer(
            name="LogoutRequest",
            fields={
                "refresh": serializers.CharField(),
            },
        ),
        responses={
            200: OpenApiResponse(
                description="Successfully logged out."
            ),
            400: OpenApiResponse(
                description="Invalid or missing refresh token."
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request):

        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(
                refresh_token
            )

            token.blacklist()

        except Exception:
            return Response(
                {
                    "detail": "Invalid refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Successfully logged out."
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):

    @extend_schema(
        responses={
            200: MeSerializer,
        },
        tags=["Authentication"],
    )
    def get(self, request):

        serializer = MeSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )