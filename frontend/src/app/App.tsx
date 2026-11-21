import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import "@/app/app.css";
import { AppToaster } from "@/app/AppToaster";
import { router } from "@/app/router";
import { ThemeProvider } from "@/app/ThemeProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { TooltipProvider } from "@/components/ui/tooltip";
import { queryClient } from "@/lib/query";

export function App() {
  return (
    <ErrorBoundary scope="aplikacja">
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <TooltipProvider delayDuration={200}>
            <RouterProvider router={router} />
            <AppToaster />
          </TooltipProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
