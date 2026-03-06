from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


# Register also logs the user in immediately so the SPA
# can continue without forcing a second manual login step.
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    password2 = request.data.get("password2") or ""

    if not username:
        return Response({"ok": False, "error": "username required"}, status=400)
    if len(password) < 6:
        return Response({"ok": False, "error": "password too short (>=6)"}, status=400)
    if password != password2:
        return Response({"ok": False, "error": "passwords do not match"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "error": "username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    login(request, user)
    return Response({"ok": True, "username": user.username})


# Separate CSRF bootstrap endpoint for the SPA frontend.
# Vue first requests a CSRF token, then sends it back on login/logout writes.
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


# Session-based auth is used here instead of token auth
# to stay aligned with Django's built-in authentication flow.
@api_view(["POST"])
@permission_classes([AllowAny])
def session_login(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"ok": False, "error": "Invalid username/password"}, status=400)
    login(request, user)
    return Response({"ok": True, "username": user.username})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_logout(request):
    logout(request)
    return Response({"ok": True})


# Lightweight session check used by the frontend router guard
# and header UI to confirm the current authenticated user.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "ok": True,
        "id": user.id,
        "username": user.username,
    })