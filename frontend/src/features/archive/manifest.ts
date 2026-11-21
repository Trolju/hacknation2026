import { Library } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "archive",
  path: "archiwum",
  label: "Archiwum spraw",
  description: "Wyszukiwanie podobnych spraw archiwalnych i gotowych rozstrzygnięć.",
  icon: Library,
  order: 30,
  component: () => import("@/features/archive/Page"),
};

export default manifest;
