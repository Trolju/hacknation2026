/**
 * Klient HTTP — jedno miejsce, w którym rozmawiamy z backendem.
 *
 * Kontrakt: `contracts/openapi.yaml`. Błędy backendu mają kształt
 * `{ code, message, details }` i są zamieniane na `ApiError`.
 */

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details ?? {};
  }
}

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

const TOKEN_KEY = "asystent.token";

/** Token sesji — `localStorage` bywa niedostępny (tryb prywatny, brak zgody). */
export function getToken(): string | null {
  try {
    return globalThis.localStorage?.getItem(TOKEN_KEY) ?? null;
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) globalThis.localStorage?.setItem(TOKEN_KEY, token);
    else globalThis.localStorage?.removeItem(TOKEN_KEY);
  } catch {
    /* brak dostępu do magazynu — sesja zostaje tylko w pamięci Reacta */
  }
}

/**
 * Nagłówki z tokenem sesji.
 *
 * Dla wywołań, które omijają `request`: wgranie pliku idzie przez `XMLHttpRequest`
 * (tylko tak pokażemy postęp), a eksport zwraca plik, nie JSON. Bez tego przy
 * `AUTH_ENABLED=true` oba kończą się 401.
 */
export function authHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const token = getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = authHeaders(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    let body: ApiErrorBody = {
      code: "http_error",
      message: `Błąd ${response.status}`,
    };
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      /* odpowiedź bez JSON — zostaje komunikat domyślny */
    }
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
    }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export function queryString(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}
