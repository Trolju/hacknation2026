import { Settings } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "settings",
  path: "ustawienia",
  label: "Ustawienia",
  description: "Tryb modułów, model językowy i stan środowiska.",
  icon: Settings,
  order: 90,
  component: () => import("@/features/settings/Page"),
};

export default manifest;
