/**
 * Hooki React Query modułu uwierzytelniania.
 *
 * Kontrakt: `contracts/openapi.yaml` (`/api/auth/*`). Token trzyma
 * `lib/api.ts` — tutaj tylko logowanie i odczyt tożsamości.
 */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type AuthUser = {
  initials: string;
  name: string;
  role: string;
  department_id: string | null;
};

export type Session = {
  token: string;
  user: AuthUser;
  expires_at: string;
};

export type LoginInput = {
  initials: string;
  pin: string;
};

/** Urzędnicy do wyboru na ekranie logowania — bez PIN-ów. */
export function useAuthUsers() {
  return useQuery({
    queryKey: ["auth", "users"],
    queryFn: () => api.get<AuthUser[]>("/auth/users"),
    staleTime: 5 * 60_000,
  });
}

/** Logowanie po inicjałach i PIN-ie. */
export function useLogin() {
  return useMutation({
    mutationFn: (input: LoginInput) => api.post<Session>("/auth/login", input),
  });
}

/**
 * Tożsamość zalogowanego urzędnika.
 *
 * Przy `AUTH_ENABLED=false` backend zwraca pierwszego użytkownika z fixtures,
 * więc ekran logowania nie pojawia się wcale — demo działa bez wpisywania PIN-u.
 */
export function useMe() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<AuthUser>("/auth/me"),
    retry: false,
    staleTime: 5 * 60_000,
  });
}
