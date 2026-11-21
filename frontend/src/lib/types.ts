/** Typy współdzielone — lustro `contracts/openapi.yaml`. */

import type { Urgency } from "@/lib/format";

export type CaseStatus =
  | "nowy"
  | "zapytania_wyslane"
  | "kwerenda"
  | "przygotowana_odpowiedz"
  | "odpowiedz_wyslana";

export type ApplicantType =
  | "osoba_fizyczna"
  | "organizacja"
  | "media"
  | "inne";

export type Case = {
  id: string;
  case_number: string;
  ordinal: number;
  subject: string;
  inflow_date: string;
  deadline: string;
  response_date: string | null;
  handler_initials: string;
  status: CaseStatus;
  year: number;
  days_remaining: number;
  urgency: Urgency;
  applicant_type: ApplicantType;
  source_document_id: string | null;
  /** Łączne przedłużenie terminu w kwerendzie, w dniach. `null` = nigdy nie była. */
  kwerenda_days: number | null;
  created_at: string;
  updated_at: string;
};

export type CaseDetail = Case & {
  notes: string | null;
  department_ids: string[];
  document_ids: string[];
};

export type HistoryEntry = {
  id: string;
  case_id: string;
  at: string;
  actor: string;
  action: string;
  from_value: string | null;
  to_value: string | null;
  note: string | null;
};

export type Department = {
  id: string;
  name: string;
  kind: "wydzial" | "biuro" | "referat";
  keywords: string[];
  url: string | null;
};

export type DepartmentSuggestion = {
  department_id: string;
  name: string;
  confidence: number;
  rationale: string;
  matched_terms: string[];
};

export type SimilarCase = {
  archive_id: string;
  case_number: string;
  subject: string;
  year: number | null;
  score: number;
  snippet: string;
  matched_terms: string[];
  response_excerpt: string;
};

export type Citation = {
  ref: number;
  source_type: "document" | "archive" | "statute" | "department_reply";
  source_id: string;
  label: string;
  excerpt: string;
};

export type Draft = {
  id: string;
  case_id: string;
  title: string;
  body: string;
  citations: Citation[];
  unsupported: string[];
  created_at: string;
  updated_at: string | null;
};

export type Span = {
  start: number;
  end: number;
  text: string;
  category: string;
  confidence: number;
  source: "regex" | "ner" | "llm";
};

export type Document = {
  id: string;
  kind: string;
  filename: string;
  title: string | null;
  mime: string;
  size_bytes: number;
  status: "pending" | "parsed" | "indexed" | "failed";
  error: string | null;
  case_id: string | null;
  chunk_count: number;
  created_at: string;
};
