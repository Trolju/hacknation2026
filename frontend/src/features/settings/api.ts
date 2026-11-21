/**
 * Hooki ekranu ustawień (WS7).
 *
 * Typy są zdefiniowane lokalnie, bo `src/lib/types.ts` jest zamrożony i nie
 * zawiera DTO warstwy modeli. Kształt odpowiada `contracts/openapi.yaml`.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type ModuleMode = "fake" | "real";

export type AppMeta = {
  name: string;
  version: string;
  offline: boolean;
  module_modes: Record<string, ModuleMode>;
};

export type InferenceProvider =
  | "fake"
  | "openai"
  | "mistral"
  | "llamacpp"
  | "ollama";

export type InferenceStatus = "ok" | "degraded" | "down";

export type InferenceHealth = {
  provider: InferenceProvider;
  model: string;
  status: InferenceStatus;
  offline: boolean;
  latency_ms: number | null;
  message: string | null;
};

export type ModelInfo = {
  id: string;
  label: string;
  provider: string;
  local: boolean;
  size_gb: number | null;
  recommended: boolean;
};

export type InferenceTestResult = {
  ok: boolean;
  latency_ms: number;
  output: string;
  error: string | null;
};

export const settingsKeys = {
  meta: ["meta"] as const,
  inferenceHealth: ["inference", "health"] as const,
  inferenceModels: ["inference", "models"] as const,
};

/** Metadane aplikacji: wersja, tryb offline i tryb każdego modułu. */
export function useAppMeta() {
  return useQuery({
    queryKey: settingsKeys.meta,
    queryFn: () => api.get<AppMeta>("/meta"),
  });
}

/** Stan warstwy modeli — backend mierzy opóźnienie realnym wywołaniem serwera. */
export function useInferenceHealth() {
  return useQuery({
    queryKey: settingsKeys.inferenceHealth,
    queryFn: () => api.get<InferenceHealth>("/inference/health"),
  });
}

/** Katalog modeli: konfiguracja aplikacji plus modele zgłoszone przez serwer. */
export function useInferenceModels() {
  return useQuery({
    queryKey: settingsKeys.inferenceModels,
    queryFn: () => api.get<ModelInfo[]>("/inference/models"),
    staleTime: 5 * 60_000,
  });
}

/** Krótki prompt do modelu — wynik zawiera opóźnienie, fragment odpowiedzi i błąd. */
export function useTestInference() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<InferenceTestResult>("/inference/test"),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: settingsKeys.inferenceHealth });
    },
  });
}
