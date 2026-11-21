/** Teksty ekranu logowania. */

export const TEXT = {
  title: "Zaloguj się",
  description:
    "Wybierz swoje konto i podaj PIN. Inicjały w sprawach pochodzą z sesji, nie z formularza.",
  initials: "Inicjały",
  pin: "PIN",
  pinHint: "W wersji demo PIN to 1234 dla każdego konta.",
  submit: "Zaloguj",
  submitting: "Logowanie…",
  failed: "Nie udało się zalogować",
  usersFailed: "Nie udało się pobrać listy urzędników",
  restoring: "Sprawdzanie sesji…",
  demo: "Wersja demonstracyjna",
} as const;

export const ROLE_LABELS: Record<string, string> = {
  referent: "Referent",
  kierownik: "Kierownik",
  naczelnik: "Naczelnik",
};

export function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}
