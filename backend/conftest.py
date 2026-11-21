"""Izolacja testów od lokalnej konfiguracji.

`backend/.env` należy do dewelopera: trzyma klucze API i wybrane tryby modułów.
Testy nie mogą go czytać — inaczej zależą od maszyny, a przy prawdziwym kluczu
zaczynają wychodzić do sieci (np. `LlmDrafting` woła wtedy model w teście E2E).

Zmienna ustawiana jest na poziomie modułu, nie w fixture: `app.core.settings`
tworzy singleton `settings` już przy imporcie, więc konfiguracja musi być
gotowa, zanim ktokolwiek zaimportuje `app`.
"""

from __future__ import annotations

import os

# Pusty `ENV_FILE` wyłącza czytanie pliku — patrz `app.core.settings`.
os.environ["ENV_FILE"] = ""

# Testy wołają API bez logowania. `current_user` zwraca wtedy pierwszego
# użytkownika z `fixtures/users.json`, więc `handler_initials` nadal pochodzi
# z tożsamości. Testy samego logowania włączają auth przez `monkeypatch`.
os.environ["AUTH_ENABLED"] = "false"
