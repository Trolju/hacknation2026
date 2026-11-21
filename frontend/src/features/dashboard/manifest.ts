import { LayoutDashboard } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "dashboard",
  path: "",
  label: "Pulpit",
  description: "Przegląd terminów, zaległości i ostatniej aktywności.",
  icon: LayoutDashboard,
  order: 0,
  component: () => import("@/features/dashboard/Page"),
};

export default manifest;
