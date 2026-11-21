"""Endpointy logowania i tożsamości."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.modules.auth.deps import current_user
from app.modules.auth.models import LoginRequest, Session, User
from app.modules.auth.service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=Session)
def login(req: LoginRequest) -> Session:
    """Logowanie po inicjałach i PIN-ie — zwraca token sesji."""
    return AuthService().login(req)


@router.get("/me", response_model=User)
def me(user: User = Depends(current_user)) -> User:
    """Tożsamość zalogowanego urzędnika."""
    return user


@router.get("/users", response_model=list[User])
def users() -> list[User]:
    """Urzędnicy do wyboru na ekranie logowania — bez PIN-ów."""
    return AuthService().users()
