/**
 * Komunikaty błędów API po polsku.
 *
 * Backend zwraca `{code, message, details}` — `message` jest już po polsku
 * i zwykle najdokładniejszy, więc wygrywa. Mapowanie po `code` wchodzi wtedy,
 * gdy serwer zwrócił sam kod HTTP (np. brama przed aplikacją) albo gdy
 * odpowiedź nie dotarła wcale.
 */

import { ApiError } from "@/lib/api";

export const API_ERROR_MESSAGES: Record<string, string> = {
  not_found: "Nie znaleziono danych. Mogły zostać usunięte albo adres jest nieaktualny.",
  validation_failed: "Dane nie przeszły walidacji. Sprawdź wypełnione pola.",
  conflict: "Operacja jest sprzeczna z aktualnym stanem sprawy.",
  invalid_transition: "Ta zmiana stanu nie jest dozwolona. Sprawdź dozwolone przejścia.",
  unsupported_media_type: "Nieobsługiwany format pliku. Dozwolone są PDF, DOCX, TXT i MD.",
  payload_too_large: "Plik jest za duży. Limit wynosi 10 MB.",
  offline_violation: "Moduł działa w trybie offline i nie może wykonać tej operacji.",
  bad_request: "Serwer odrzucił żądanie. Sprawdź wprowadzone dane.",
  http_error: "Serwer zwrócił błąd. Spróbuj ponownie za chwilę.",
  network_error: "Brak połączenia z serwerem. Sprawdź, czy backend działa.",
};

export const API_ERROR_TITLES: Record<string, string> = {
  not_found: "Nie znaleziono danych",
  validation_failed: "Błąd walidacji",
  conflict: "Konflikt danych",
  invalid_transition: "Niedozwolona zmiana stanu",
  unsupported_media_type: "Nieobsługiwany plik",
  payload_too_large: "Plik za duży",
  offline_violation: "Tryb offline",
  network_error: "Brak połączenia",
};

export const FALLBACK_ERROR_MESSAGE = "Wystąpił nieoczekiwany błąd. Spróbuj ponownie.";
export const FALLBACK_ERROR_TITLE = "Wystąpił błąd";

/** `Błąd 500` to komunikat zastępczy klienta HTTP, nie treść od serwera. */
const GENERIC_MESSAGE = /^Błąd \d{3}$/;

export function apiErrorCode(error: unknown): string | null {
  if (error instanceof ApiError) return error.code;
  if (error instanceof TypeError) return "network_error";
  return null;
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const mapped = API_ERROR_MESSAGES[error.code];
    const message = error.message?.trim() ?? "";
    if (!message || GENERIC_MESSAGE.test(message)) {
      return mapped ?? API_ERROR_MESSAGES.http_error;
    }
    return message;
  }
  if (error instanceof TypeError) return API_ERROR_MESSAGES.network_error;
  if (error instanceof Error) return error.message.trim() || FALLBACK_ERROR_MESSAGE;
  return FALLBACK_ERROR_MESSAGE;
}

export function apiErrorTitle(error: unknown): string {
  const code = apiErrorCode(error);
  if (code) return API_ERROR_TITLES[code] ?? FALLBACK_ERROR_TITLE;
  return FALLBACK_ERROR_TITLE;
}
