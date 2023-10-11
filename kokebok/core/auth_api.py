from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from ninja import Router, Schema

router = Router()


class LoginDetails(Schema):
    username: str
    password: str


class IsAuthenticated(Schema):
    is_authenticated: bool


@router.get("get-csrf")
def get_csrf(request: HttpRequest, response: HttpResponse):
    response["X-CSRFToken"] = get_token(request)
    return ""


@router.post("login", response={200: str, 400: str})
def do_login(request, details: LoginDetails):
    user = authenticate(username=details.username, password=details.password)

    if user is None:
        return 400, "Invalid credentials"

    login(request, user)
    return ""


@router.get("logout", response={200: str, 400: str})
def do_logout(request):
    if not request.user.is_authenticated:
        return 400, "You are not logged in."

    logout(request)
    return ""


@router.get("session", response=IsAuthenticated)
def session_view(request):
    get_token(request)
    return {"is_authenticated": request.user.is_authenticated}
