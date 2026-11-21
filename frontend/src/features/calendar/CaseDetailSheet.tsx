import { useEffect, useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";

import { ErrorState, LoadingState } from "@/components/States";
import { StatusBadge, UrgencyBadge } from "@/components/StatusBadges";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { t } from "@/features/calendar/i18n";
import { parseKwerendaDays } from "@/features/calendar/kwerenda";
import {
  transitionOptions,
  type TransitionOption,
} from "@/features/calendar/statusMachine";
import {
  formatDate,
  formatDateTime,
  relativeDays,
  STATUS_LABEL,
} from "@/lib/format";
import { useCase, useCaseHistory, useTransitionCase } from "@/lib/hooks";
import type { HistoryEntry } from "@/lib/types";

const ACTION_LABEL: Record<string, string> = {
  created: t.detail.actions.created,
  field_update: t.detail.actions.field_update,
  status_change: t.detail.actions.status_change,
};

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

function transitionLabel(option: TransitionOption): string {
  const label = STATUS_LABEL[option.to] ?? option.to;
  if (option.kind === "backward") return t.detail.transition.backward(label);
  if (option.kind === "skip") return t.detail.transition.skip(label);
  return t.detail.transition.forward(label);
}

function HistoryItem({ entry }: { entry: HistoryEntry }) {
  return (
    <li className="rounded-lg border p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium">
          {ACTION_LABEL[entry.action] ?? entry.action}
        </span>
        <span className="text-xs text-muted-foreground">
          {formatDateTime(entry.at)}
        </span>
      </div>
      {entry.from_value || entry.to_value ? (
        <p className="mt-1 text-xs text-muted-foreground">
          {STATUS_LABEL[entry.from_value ?? ""] ?? entry.from_value ?? "—"} →{" "}
          {STATUS_LABEL[entry.to_value ?? ""] ?? entry.to_value ?? "—"}
        </p>
      ) : null}
      {entry.note ? <p className="mt-1 text-sm">{entry.note}</p> : null}
      <p className="mt-1 text-xs text-muted-foreground">{entry.actor}</p>
    </li>
  );
}

type CaseDetailSheetProps = {
  caseId: string | null;
  onClose: () => void;
};

export function CaseDetailSheet({ caseId, onClose }: CaseDetailSheetProps) {
  // Podczas animacji zamykania `caseId` jest już puste — trzymamy ostatnie
  // otwarte zgłoszenie, żeby panel nie mrugnął pustką.
  const lastCaseId = useRef<string | null>(null);
  if (caseId) lastCaseId.current = caseId;
  const shownCaseId = caseId ?? lastCaseId.current;

  const detail = useCase(shownCaseId ?? undefined);
  const history = useCaseHistory(shownCaseId ?? undefined);
  const transition = useTransitionCase();

  const [note, setNote] = useState("");
  const [kwerendaDays, setKwerendaDays] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    setNote("");
    setKwerendaDays("");
    setFormError(null);
    setApiError(null);
  }, [caseId]);

  const runTransition = (option: TransitionOption) => {
    if (!caseId) return;
    if (option.requiresNote && note.trim() === "") {
      setFormError(t.detail.transition.noteRequired);
      return;
    }
    const parsed = parseKwerendaDays(kwerendaDays);
    if (option.to === "kwerenda" && !parsed.ok) {
      setFormError(t.detail.transition.daysInvalid);
      return;
    }
    const extendsDeadline = option.to === "kwerenda" && parsed.ok ? parsed.days : undefined;
    setFormError(null);
    setApiError(null);
    transition.mutate(
      {
        caseId,
        to: option.to,
        note: note.trim() || undefined,
        kwerendaDays: extendsDeadline,
      },
      {
        onSuccess: () => {
          setNote("");
          setKwerendaDays("");
          toast.success(t.detail.transition.saved);
        },
        onError: (error) => {
          setApiError(
            error instanceof Error ? error.message : t.detail.transition.failed,
          );
        },
      },
    );
  };

  const data = detail.data;
  const options = data ? transitionOptions(data.status) : [];
  const historyEntries = history.data ?? [];

  return (
    <Sheet
      open={Boolean(caseId)}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent
        side="right"
        className="w-full overflow-y-auto sm:max-w-2xl"
      >
        <SheetHeader>
          <SheetTitle>{data?.case_number ?? t.detail.title}</SheetTitle>
          <SheetDescription>
            {data?.subject ?? t.detail.loading}
          </SheetDescription>
        </SheetHeader>

        {detail.isLoading ? (
          <div className="mt-4">
            <LoadingState rows={4} />
          </div>
        ) : detail.isError ? (
          <div className="mt-4">
            <ErrorState
              error={detail.error}
              onRetry={() => void detail.refetch()}
            />
          </div>
        ) : data ? (
          <div className="mt-4 space-y-6">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={data.status} />
              <UrgencyBadge
                urgency={data.urgency}
                days={data.days_remaining}
              />
              {data.status === "odpowiedz_wyslana" ? null : (
                <span className="text-xs text-muted-foreground">
                  {relativeDays(data.days_remaining)}
                </span>
              )}
            </div>

            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label={t.detail.fields.ordinal}>{data.ordinal}</Field>
              <Field label={t.detail.fields.year}>{data.year}</Field>
              <Field label={t.detail.fields.inflow}>
                {formatDate(data.inflow_date)}
              </Field>
              <Field label={t.detail.fields.deadline}>
                {formatDate(data.deadline)}
              </Field>
              <Field label={t.detail.fields.responseDate}>
                {formatDate(data.response_date)}
              </Field>
              <Field label={t.detail.fields.days}>
                <span className="tabular-nums">{data.days_remaining}</span>
              </Field>
              <Field label={t.detail.fields.handler}>
                {data.handler_initials || "—"}
              </Field>
              <Field label={t.detail.fields.applicant}>
                {t.detail.applicantTypes[data.applicant_type]}
              </Field>
              <Field label={t.detail.fields.departments}>
                {data.department_ids.length > 0
                  ? data.department_ids.join(", ")
                  : "—"}
              </Field>
              <Field label={t.detail.fields.notes}>{data.notes || "—"}</Field>
            </dl>

            <Separator />

            <section>
              <h3 className="mb-1 text-sm font-semibold">
                {t.detail.transition.title}
              </h3>
              <p className="mb-2 text-xs text-muted-foreground">
                {t.detail.transition.hint}
              </p>
              {data.status === "odpowiedz_wyslana" ? (
                <p className="mb-2 text-xs text-amber-700">
                  {t.detail.transition.closedHint}
                </p>
              ) : null}

              <div className="flex flex-wrap gap-2">
                {options.map((option) => (
                  <Button
                    key={option.to}
                    size="sm"
                    variant={option.kind === "backward" ? "outline" : "default"}
                    disabled={transition.isPending}
                    onClick={() => runTransition(option)}
                  >
                    {transitionLabel(option)}
                  </Button>
                ))}
              </div>

              <div className="mt-3 space-y-1">
                <Label htmlFor="transition-note">
                  {t.detail.transition.noteLabel}
                </Label>
                <Textarea
                  id="transition-note"
                  value={note}
                  placeholder={t.detail.transition.notePlaceholder}
                  onChange={(event) => {
                    setNote(event.target.value);
                    if (formError) setFormError(null);
                  }}
                />
              </div>

              {options.some((option) => option.to === "kwerenda") ? (
                <div className="mt-3 space-y-1">
                  <Label htmlFor="kwerenda-days">
                    {t.detail.transition.daysLabel}
                  </Label>
                  <Input
                    id="kwerenda-days"
                    type="number"
                    min={1}
                    max={60}
                    inputMode="numeric"
                    value={kwerendaDays}
                    placeholder={t.detail.transition.daysPlaceholder}
                    onChange={(event) => {
                      setKwerendaDays(event.target.value);
                      if (formError) setFormError(null);
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t.detail.transition.daysHint}
                  </p>
                </div>
              ) : null}

              {data.kwerenda_days ? (
                <p className="mt-3 text-xs text-muted-foreground">
                  {t.detail.transition.daysApplied(data.kwerenda_days)}
                </p>
              ) : null}

              {formError ? (
                <p className="mt-2 text-sm text-destructive" role="alert">
                  {formError}
                </p>
              ) : null}

              {apiError ? (
                <Alert variant="destructive" className="mt-3">
                  <AlertTitle>{t.detail.transition.failed}</AlertTitle>
                  <AlertDescription>{apiError}</AlertDescription>
                </Alert>
              ) : null}
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 text-sm font-semibold">
                {t.detail.history}
              </h3>
              {history.isLoading ? (
                <p className="text-sm text-muted-foreground">
                  {t.detail.historyLoading}
                </p>
              ) : history.isError ? (
                <ErrorState
                  error={history.error}
                  onRetry={() => void history.refetch()}
                />
              ) : historyEntries.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t.detail.historyEmpty}
                </p>
              ) : (
                <ol className="space-y-2">
                  {historyEntries.map((entry) => (
                    <HistoryItem key={entry.id} entry={entry} />
                  ))}
                </ol>
              )}
            </section>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
