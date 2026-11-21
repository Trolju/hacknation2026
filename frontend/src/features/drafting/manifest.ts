import { PenLine } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "drafting",
  path: "odpowiedzi",
  label: "Generator odpowiedzi",
  description: "Projekt odpowiedzi z cytowaniami, edycją i eksportem.",
  icon: PenLine,
  order: 50,
  component: () => import("@/features/drafting/Page"),
};

export default manifest;
