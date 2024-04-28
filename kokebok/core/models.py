from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .managers import UserManager

username_validator = UnicodeUsernameValidator()


class User(AbstractBaseUser, PermissionsMixin):
    """
    Bare-bones user class.
    Contains the following fields:
        id, password, last_login,
        is_superuser, groups, user_permissions
        username, is_staff
    """

    username = models.CharField(
        max_length=150, unique=True, validators=[username_validator]
    )
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
