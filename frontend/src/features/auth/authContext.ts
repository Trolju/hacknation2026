import { createContext } from "react";

import type { AuthUser, Session } from "./api";

export type AuthState = {
  user: AuthUser | null;
  /** Trwa odczyt tożsamości — nie pokazuj jeszcze ani logowania, ani aplikacji. */
  restoring: boolean;
  /** Backend działa bez logowania (`AUTH_ENABLED=false`) — chowamy wylogowanie. */
  authDisabled: boolean;
  signIn: (session: Session) => void;
  signOut: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);
