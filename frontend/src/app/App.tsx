import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import "@/app/app.css";
import { AppToaster } from "@/app/AppToaster";
import { router } from "@/app/router";
import { ThemeProvider } from "@/app/ThemeProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/features/auth/context";
import { TEXT as AUTH_TEXT } from "@/features/auth/i18n";
import LoginPage from "@/features/auth/LoginPage";
import { useAuth } from "@/features/auth/useAuth";
import { queryClient } from "@/lib/query";

/**
 * Bramka sesji — dopóki nie wiemy, kto pracuje, nie pokazujemy ani aplikacji,
 * ani logowania. Bez tego ekran mruga formularzem przy każdym odświeżeniu.
 */
function AuthGate() {
  const { user, restoring } = useAuth();

  if (restoring) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        {AUTH_TEXT.restoring}
      </div>
    );
  }
  if (!user) return <LoginPage />;
  return <RouterProvider router={router} />;
}

export function App() {
  return (
    <ErrorBoundary scope="aplikacja">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ThemeProvider>
            <TooltipProvider delayDuration={200}>
              <AuthGate />
              <AppToaster />
            </TooltipProvider>
          </ThemeProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
