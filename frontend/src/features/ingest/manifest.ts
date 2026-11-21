import { FileText } from "lucide-react";

import type { FeatureManifest } from "@/app/registry";

const manifest: FeatureManifest = {
  id: "ingest",
  path: "dokumenty",
  label: "Dokumenty",
  description: "Wgrywanie i odczyt wniosków, odpowiedzi wydziałów oraz aktów prawnych.",
  icon: FileText,
  order: 20,
  component: () => import("@/features/ingest/Page"),
};

export default manifest;
