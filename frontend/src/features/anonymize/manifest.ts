import { ShieldCheck } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "anonymize",
  path: "anonimizacja",
  label: "Anonimizacja",
  description: "Wykrywanie i usuwanie danych osobowych z dokumentów.",
  icon: ShieldCheck,
  order: 60,
  component: () => import("@/features/anonymize/Page"),
};

export default manifest;
