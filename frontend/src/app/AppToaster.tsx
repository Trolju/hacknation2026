import { useTheme } from "@/app/theme";
import { Toaster } from "@/components/ui/sonner";

/** Toaster reagujący na motyw — kolory toastów idą za klasą `dark`. */
export function AppToaster() {
  const { theme } = useTheme();
  return <Toaster theme={theme} />;
}
