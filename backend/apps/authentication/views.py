from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    MeSerializer,
    SetPasswordSerializer,
)

from django.utils.http import (
    urlsafe_base64_encode,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
    inline_serializer,
)

from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from .services import AccountService

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

@extend_schema(
    parameters=[
        OpenApiParameter(
            name="uidb64",
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description="URL-safe encoded user ID.",
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description="One-time password setup token.",
        ),
    ],
)
class SetPasswordView(APIView):

    permission_classes = [
        AllowAny,
    ]

    @extend_schema(
        operation_id="set_password",
        summary="Set account password",
        description=(
            "Set the password for an invited account "
            "using a valid one-time setup token."
        ),
        request=SetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password successfully set."
            ),
            400: OpenApiResponse(
                description="Invalid or expired setup link."
            ),
        },
        tags=["Authentication"],
    )
    def post(
        self,
        request,
        uidb64,
        token,
    ):

        try:
            user = (
                AccountService
                .validate_password_setup_token(
                    uidb64=uidb64,
                    token=token,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------
        # Safeguard: Block already active users
        # -----------------------------------
        if user.has_usable_password():
            return Response(
                {
                    "detail": "This account has already been set up."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SetPasswordSerializer(
            data=request.data,
            context={
                "user": user,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            AccountService.set_password(
                user=user,
                password=serializer.validated_data[
                    "password"
                ],
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Password successfully set."
            },
            status=status.HTTP_200_OK,
        )