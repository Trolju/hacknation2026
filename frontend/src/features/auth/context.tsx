/**
 * Provider sesji — jedno miejsce, w którym aplikacja wie, kto pracuje.
 *
 * Źródłem prawdy jest `/api/auth/me`. Przy `AUTH_ENABLED=false` backend zwraca
 * pierwszego urzędnika z fixtures, więc ekran logowania się nie pojawia,
 * a wylogowanie nie ma czego unieważnić — stąd flaga `authDisabled`.
 */

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { getToken, setToken } from "@/lib/api";

import { useMe } from "./api";
import type { Session } from "./api";
import { AuthContext } from "./authContext";
import type { AuthUser } from "./api";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authDisabled, setAuthDisabled] = useState(false);
  const me = useMe();

  useEffect(() => {
    if (me.isSuccess) {
      setUser(me.data);
      // Sukces bez tokenu oznacza, że backend nie wymaga logowania.
      setAuthDisabled(getToken() === null);
    } else if (me.isError) {
      setUser(null);
      setAuthDisabled(false);
    }
  }, [me.isSuccess, me.isError, me.data]);

  const signIn = useCallback(
    (session: Session) => {
      setToken(session.token);
      setUser(session.user);
      setAuthDisabled(false);
      queryClient.setQueryData(["auth", "me"], session.user);
    },
    [queryClient],
  );

  const signOut = useCallback(() => {
    setToken(null);
    setUser(null);
    queryClient.removeQueries({ queryKey: ["auth", "me"] });
  }, [queryClient]);

  const value = useMemo(
    () => ({ user, restoring: me.isLoading, authDisabled, signIn, signOut }),
    [user, me.isLoading, authDisabled, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
