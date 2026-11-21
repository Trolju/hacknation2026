import { CalendarDays } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "calendar",
  path: "kalendarz",
  label: "Kalendarz terminów",
  description: "Wnioski według terminu odpowiedzi, z filtrami i widokiem miesiąca.",
  icon: CalendarDays,
  order: 10,
  component: () => import("@/features/calendar/Page"),
};

export default manifest;
