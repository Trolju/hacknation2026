/**
 * Rejestr ekranów — odkrywany automatycznie.
 *
 * Każdy katalog w `src/features/<nazwa>/` może wystawić `manifest.ts`.
 * Nikt nie edytuje centralnej listy tras: dodanie ekranu to dodanie katalogu.
 */

import type { LucideIcon } from "lucide-react";
import type { ComponentType } from "react";

export type FeatureManifest = {
  /** Identyfikator modułu — zgodny z nazwą katalogu. */
  id: string;
  /** Ścieżka bez wiodącego ukośnika; pusty string oznacza stronę główną. */
  path: string;
  label: string;
  description: string;
  icon: LucideIcon;
  /** Kolejność w menu; mniejsza wartość wyżej. */
  order: number;
  /** Czy ekran ma być widoczny w menu. */
  hidden?: boolean;
  component: () => Promise<{ default: ComponentType }>;
};

type ManifestModule = { default: FeatureManifest };

const modules = import.meta.glob<ManifestModule>("../features/*/manifest.ts", {
  eager: true,
});

export const features: FeatureManifest[] = Object.values(modules)
  .map((module) => module.default)
  .sort((a, b) => a.order - b.order || a.label.localeCompare(b.label, "pl"));

export const visibleFeatures = features.filter((feature) => !feature.hidden);

export function findFeature(id: string): FeatureManifest | undefined {
  return features.find((feature) => feature.id === id);
}
