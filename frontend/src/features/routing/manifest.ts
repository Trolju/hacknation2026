import { Network } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "routing",
  path: "wydzialy",
  label: "Routing wydziałowy",
  description: "Wskazywanie komórek organizacyjnych i generowanie zapytań.",
  icon: Network,
  order: 40,
  component: () => import("@/features/routing/Page"),
};

export default manifest;
