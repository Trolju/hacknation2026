"""Testy logowania i tożsamości urzędnika.

Sprawdzamy dwie rzeczy, które decydują o sensie modułu:

1. token da się podrobić tylko znajomością sekretu — zmiana inicjałów,
   podpisu albo daty wygaśnięcia kończy się odmową,
2. `handler_initials` i autor przejścia pochodzą z sesji, a nie z pola
   w formularzu — inaczej każdy mógłby podpisać sprawę cudzym nazwiskiem.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.modules.auth.models import LoginRequest
from app.modules.auth.service import AuthService, Forbidden, Unauthorized


# ──────────────────────────────── serwis ───────────────────────────────────
def test_logowanie_poprawnym_pinem() -> None:
    session = AuthService().login(LoginRequest(initials="JK", pin="1234"))

    assert session.user.initials == "JK"
    assert session.user.name == "Jan Kowalski"
    assert session.token.count(".") == 2
    assert session.expires_at > datetime.now(UTC)


def test_logowanie_ignoruje_wielkosc_inicjalow() -> None:
    session = AuthService().login(LoginRequest(initials="jk", pin="1234"))

    assert session.user.initials == "JK"


def test_logowanie_zly_pin() -> None:
    with pytest.raises(Unauthorized):
        AuthService().login(LoginRequest(initials="JK", pin="9999"))


def test_logowanie_nieznane_inicjaly() -> None:
    with pytest.raises(Unauthorized):
        AuthService().login(LoginRequest(initials="ZZ", pin="1234"))


def test_weryfikacja_swiezego_tokenu() -> None:
    service = AuthService()
    session = service.login(LoginRequest(initials="AN", pin="1234"))

    user = service.verify(session.token)

    assert user.initials == "AN"
    assert user.role == "kierownik"


def test_weryfikacja_odrzuca_podmieniony_podpis() -> None:
    service = AuthService()
    session = service.login(LoginRequest(initials="JK", pin="1234"))
    initials, expiry, _ = session.token.split(".")

    with pytest.raises(Unauthorized):
        service.verify(f"{initials}.{expiry}.{'0' * 64}")


def test_weryfikacja_odrzuca_zmienione_inicjaly() -> None:
    service = AuthService()
    session = service.login(LoginRequest(initials="JK", pin="1234"))
    _, expiry, signature = session.token.split(".")

    with pytest.raises(Unauthorized):
        service.verify(f"AN.{expiry}.{signature}")


def test_weryfikacja_odrzuca_wygasly_token(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()
    monkeypatch.setattr(settings, "auth_session_hours", -1)
    session = service.login(LoginRequest(initials="JK", pin="1234"))

    with pytest.raises(Forbidden):
        service.verify(session.token)


def test_weryfikacja_odrzuca_zly_format() -> None:
    with pytest.raises(Unauthorized):
        AuthService().verify("cokolwiek")


def test_lista_uzytkownikow_bez_pinow() -> None:
    users = AuthService().users()

    assert len(users) >= 5
    assert {user.initials for user in users} >= {"JK", "AN", "PW", "MZ", "TL"}
    assert all(not hasattr(user, "pin") for user in users)


# ──────────────────────────────── API ──────────────────────────────────────
def test_api_logowanie(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"initials": "JK", "pin": "1234"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["initials"] == "JK"
    assert body["token"]


def test_api_logowanie_zly_pin(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"initials": "JK", "pin": "0000"})

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_api_me_bez_tokenu(client: TestClient, auth_on: None) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_api_me_z_tokenem(client: TestClient, auth_on: None) -> None:
    token = client.post(
        "/api/auth/login", json={"initials": "MZ", "pin": "1234"}
    ).json()["token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["initials"] == "MZ"


def test_api_me_bez_auth_zwraca_pierwszego_uzytkownika(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["initials"] == "JK"


def test_api_lista_uzytkownikow(client: TestClient) -> None:
    response = client.get("/api/auth/users")

    assert response.status_code == 200
    assert len(response.json()) >= 5


def test_odczyt_bez_tokenu_jest_zablokowany(
    client: TestClient, auth_on: None
) -> None:
    """Bramka obejmuje cały moduł, nie tylko zapis."""
    response = client.get("/api/cases")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_health_dziala_bez_tokenu(client: TestClient, auth_on: None) -> None:
    """Pasek nagłówka pyta o stan backendu jeszcze przed zalogowaniem."""
    response = client.get("/api/health")

    assert response.status_code == 200


# ──────────────────────── tożsamość w sprawach ─────────────────────────────
def test_inicjaly_w_sprawie_pochodza_z_tokenu(
    client: TestClient, auth_on: None
) -> None:
    """Pole `handler_initials` z formularza jest ignorowane."""
    token = client.post(
        "/api/auth/login", json={"initials": "PW", "pin": "1234"}
    ).json()["token"]

    response = client.post(
        "/api/cases",
        json={
            "case_number": "BKS.IV.1431.99.2026",
            "subject": "Test tożsamości",
            "inflow_date": "2026-03-16",
            "handler_initials": "XX",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["handler_initials"] == "PW"


def test_autor_przejscia_pochodzi_z_tokenu(
    client: TestClient, auth_on: None
) -> None:
    token = client.post(
        "/api/auth/login", json={"initials": "AN", "pin": "1234"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/cases",
        json={
            "case_number": "BKS.IV.1431.98.2026",
            "subject": "Test autora",
            "inflow_date": "2026-03-16",
        },
        headers=headers,
    ).json()

    response = client.post(
        f"/api/cases/{created['id']}/transition",
        json={"to": "zapytania_wyslane", "actor": "Podrobiony Urzędnik"},
        headers=headers,
    )

    assert response.status_code == 200
    history = client.get(f"/api/cases/{created['id']}/history", headers=headers).json()
    assert any(entry["actor"] == "Anna Nowak" for entry in history)
    assert all(entry["actor"] != "Podrobiony Urzędnik" for entry in history)
