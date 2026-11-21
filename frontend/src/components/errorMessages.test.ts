import { describe, expect, it } from "vitest";

import {
  API_ERROR_MESSAGES,
  FALLBACK_ERROR_MESSAGE,
  FALLBACK_ERROR_TITLE,
  apiErrorCode,
  apiErrorMessage,
  apiErrorTitle,
} from "@/components/errorMessages";
import { ApiError } from "@/lib/api";

function apiError(status: number, code: string, message: string): ApiError {
  return new ApiError(status, { code, message });
}

describe("apiErrorCode", () => {
  it("zwraca kod z odpowiedzi serwera", () => {
    expect(apiErrorCode(apiError(404, "not_found", "Nie ma"))).toBe("not_found");
  });

  it("błąd sieci zgłasza jako network_error", () => {
    expect(apiErrorCode(new TypeError("Failed to fetch"))).toBe("network_error");
  });

  it("dla nieznanego obiektu zwraca null", () => {
    expect(apiErrorCode("cokolwiek")).toBeNull();
  });
});

describe("apiErrorMessage", () => {
  it("preferuje komunikat z backendu, bo jest najbardziej konkretny", () => {
    const error = apiError(
      409,
      "invalid_transition",
      "Cofnięcie stanu wymaga notatki.",
    );
    expect(apiErrorMessage(error)).toBe("Cofnięcie stanu wymaga notatki.");
  });

  it("podmienia zastępczy komunikat HTTP na mapowanie po kodzie", () => {
    const error = apiError(404, "not_found", "Błąd 404");
    expect(apiErrorMessage(error)).toBe(API_ERROR_MESSAGES.not_found);
  });

  it("mapuje nieznany kod na komunikat ogólny", () => {
    const error = apiError(500, "cos_nowego", "Błąd 500");
    expect(apiErrorMessage(error)).toBe(API_ERROR_MESSAGES.http_error);
  });

  it("rozpoznaje brak połączenia z serwerem", () => {
    expect(apiErrorMessage(new TypeError("Failed to fetch"))).toBe(
      API_ERROR_MESSAGES.network_error,
    );
  });

  it("przepuszcza treść zwykłego błędu", () => {
    expect(apiErrorMessage(new Error("Nieoczekiwany stan"))).toBe(
      "Nieoczekiwany stan",
    );
  });

  it("dla wartości bez treści zwraca komunikat ogólny", () => {
    expect(apiErrorMessage(null)).toBe(FALLBACK_ERROR_MESSAGE);
    expect(apiErrorMessage(new Error("   "))).toBe(FALLBACK_ERROR_MESSAGE);
  });
});

describe("apiErrorTitle", () => {
  it("nazywa typ błędu po polsku", () => {
    expect(apiErrorTitle(apiError(404, "not_found", "Nie ma"))).toBe(
      "Nie znaleziono danych",
    );
    expect(apiErrorTitle(apiError(409, "invalid_transition", "Nie wolno"))).toBe(
      "Niedozwolona zmiana stanu",
    );
  });

  it("dla błędu sieci mówi o połączeniu", () => {
    expect(apiErrorTitle(new TypeError("Failed to fetch"))).toBe(
      "Brak połączenia",
    );
  });

  it("dla nieznanego błędu zwraca tytuł ogólny", () => {
    expect(apiErrorTitle(new Error("cokolwiek"))).toBe(FALLBACK_ERROR_TITLE);
  });
});

describe("słownik komunikatów", () => {
  it("każdy komunikat jest pełnym zdaniem po polsku", () => {
    for (const [code, message] of Object.entries(API_ERROR_MESSAGES)) {
      expect(message.length, code).toBeGreaterThan(10);
      expect(message, code).toMatch(/\.$/);
      expect(message, code).not.toMatch(/\b(error|failed|invalid)\b/i);
    }
  });
});
