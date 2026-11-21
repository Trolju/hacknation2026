import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, queryString } from "@/lib/api";
import type {
  Case,
  CaseDetail,
  CaseStatus,
  Department,
  DepartmentSuggestion,
  Document,
  Draft,
  HistoryEntry,
  SimilarCase,
} from "@/lib/types";

export type CaseFilters = {
  year?: number;
  status?: CaseStatus;
  q?: string;
  sort?: string;
};

export function useCases(filters: CaseFilters = {}) {
  return useQuery({
    queryKey: ["cases", filters],
    queryFn: () => api.get<Case[]>(`/cases${queryString(filters)}`),
  });
}

export function useCaseYears() {
  return useQuery({
    queryKey: ["cases", "years"],
    queryFn: () => api.get<number[]>("/cases/years"),
  });
}

export function useCase(caseId: string | undefined) {
  return useQuery({
    queryKey: ["case", caseId],
    queryFn: () => api.get<CaseDetail>(`/cases/${caseId}`),
    enabled: Boolean(caseId),
  });
}

export function useCaseHistory(caseId: string | undefined) {
  return useQuery({
    queryKey: ["case", caseId, "history"],
    queryFn: () => api.get<HistoryEntry[]>(`/cases/${caseId}/history`),
    enabled: Boolean(caseId),
  });
}

export function useTransitionCase() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      caseId: string;
      to: CaseStatus;
      note?: string;
      kwerendaDays?: number;
    }) =>
      api.post<Case>(`/cases/${input.caseId}/transition`, {
        to: input.to,
        note: input.note,
        kwerenda_days: input.kwerendaDays,
      }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cases"] });
      void client.invalidateQueries({ queryKey: ["case"] });
      // Zamknięcie sprawy dopisuje ją do archiwum — lista musi się odświeżyć.
      void client.invalidateQueries({ queryKey: ["archive"] });
      // Zmiana terminu albo zamknięcie sprawy zmienia też listę przypomnień.
      void client.invalidateQueries({ queryKey: ["reminders"] });
    },
  });
}

export function useDepartments() {
  return useQuery({
    queryKey: ["departments"],
    queryFn: () => api.get<Department[]>("/routing/departments"),
    staleTime: 5 * 60_000,
  });
}

export function useSuggestDepartments() {
  return useMutation({
    mutationFn: (input: { text: string; k?: number }) =>
      api.post<DepartmentSuggestion[]>("/routing/suggest", {
        text: input.text,
        k: input.k ?? 3,
      }),
  });
}

export function useSimilarCases() {
  return useMutation({
    mutationFn: (input: { text: string; k?: number }) =>
      api.post<SimilarCase[]>("/archive/similar", {
        text: input.text,
        k: input.k ?? 5,
      }),
  });
}

export function useDocuments(caseId?: string) {
  return useQuery({
    queryKey: ["documents", caseId ?? "all"],
    queryFn: () => api.get<Document[]>(`/documents${queryString({ case_id: caseId })}`),
  });
}

export function useDraft(caseId: string | undefined) {
  return useQuery({
    queryKey: ["draft", caseId],
    queryFn: () => api.get<Draft>(`/drafting/${caseId}`),
    enabled: Boolean(caseId),
    retry: false,
  });
}

export function useCreateDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (caseId: string) =>
      api.post<Draft>("/drafting/draft", { case_id: caseId }),
    onSuccess: (draft) => {
      client.setQueryData(["draft", draft.case_id], draft);
    },
  });
}

export function useSaveDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { draftId: string; body: string; title?: string }) =>
      api.patch<Draft>(`/drafting/${input.draftId}`, {
        body: input.body,
        title: input.title,
      }),
    onSuccess: (draft) => {
      client.setQueryData(["draft", draft.case_id], draft);
    },
  });
}
