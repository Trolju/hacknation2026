import { ArrowRight, Copy, Download, FileText, Network } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { StatusBadge, UrgencyBadge } from "@/components/StatusBadges";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { formatShortDate } from "@/lib/format";
import { useCases } from "@/lib/hooks";
import type { DepartmentSuggestion } from "@/lib/types";
import { cn } from "@/lib/utils";

import {
  MIN_TEXT_LENGTH,
  copyText,
  downloadText,
  inquiryFileName,
  useDepartments,
  useInquiryPreview,
  useSuggestDepartments,
} from "./api";
import { TEXT } from "./i18n";
import {
  defaultSelection,
  isAllSelected,
  pruneSelection,
  toggleId,
} from "./selection";
import { useDebouncedValue } from "./useDebouncedValue";

/** Wartość `Select` oznaczająca „nie bierz sprawy z kalendarza”. */
const MANUAL_CASE = "manual";

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function confidenceVariant(value: number): "default" | "secondary" | "outline" {
  if (value >= 0.75) return "default";
  if (value >= 0.45) return "secondary";
  return "outline";
}

function SuggestionRow({
  suggestion,
  kind,
  checked,
  onToggle,
}: {
  suggestion: DepartmentSuggestion;
  kind?: string;
  checked: boolean;
  onToggle: () => void;
}) {
  const inputId = `komorka-${suggestion.department_id}`;
  return (
    <li
      className={cn(
        "rounded-lg border p-3 transition-colors",
        checked ? "border-primary/60 bg-primary/5" : "bg-card",
      )}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          id={inputId}
          checked={checked}
          onCheckedChange={onToggle}
          className="mt-1"
        />
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Label htmlFor={inputId} className="cursor-pointer text-sm font-medium">
              {suggestion.name}
            </Label>
            {kind ? (
              <Badge variant="outline" className="font-normal">
                {TEXT.kindLabel[kind] ?? kind}
              </Badge>
            ) : null}
            <Badge
              variant={confidenceVariant(suggestion.confidence)}
              className="ml-auto tabular-nums"
            >
              {TEXT.confidence} {percent(suggestion.confidence)}
            </Badge>
          </div>
          <Progress
            value={suggestion.confidence * 100}
            aria-label={`${TEXT.confidence}: ${percent(suggestion.confidence)}`}
          />
          <p className="text-sm text-muted-foreground">{suggestion.rationale}</p>
          {suggestion.matched_terms.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-muted-foreground">
                {TEXT.matchedTerms}:
              </span>
              {suggestion.matched_terms.map((term) => (
                <Badge key={term} variant="secondary" className="font-normal">
                  {term}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </li>
  );
}

export default function RoutingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const caseParam = searchParams.get("case");

  const casesQuery = useCases({ sort: "deadline_asc" });
  const cases = useMemo(() => casesQuery.data ?? [], [casesQuery.data]);

  const departmentsQuery = useDepartments();
  const kindById = useMemo(() => {
    const map = new Map<string, string>();
    for (const department of departmentsQuery.data ?? []) {
      map.set(department.id, department.kind);
    }
    return map;
  }, [departmentsQuery.data]);

  const [caseId, setCaseId] = useState<string | null>(caseParam);
  const [text, setText] = useState("");
  const [manualSelection, setManualSelection] = useState<string[] | null>(null);

  // Wejście z linku `?case=<id>` (np. z kalendarza) wypełnia treść przedmiotem.
  const appliedParam = useRef<string | null>(null);
  useEffect(() => {
    if (!caseParam || appliedParam.current === caseParam) return;
    const found = cases.find((item) => item.id === caseParam);
    if (!found) return;
    appliedParam.current = caseParam;
    setCaseId(found.id);
    setText(found.subject);
    setManualSelection(null);
  }, [caseParam, cases]);

  const debouncedText = useDebouncedValue(text);
  const suggestionsQuery = useSuggestDepartments(debouncedText);
  const suggestions = useMemo(
    () => suggestionsQuery.data ?? [],
    [suggestionsQuery.data],
  );

  const fallbackSelection = useMemo(() => defaultSelection(suggestions), [suggestions]);
  const selectedIds = useMemo(
    () => pruneSelection(manualSelection ?? fallbackSelection, suggestions),
    [manualSelection, fallbackSelection, suggestions],
  );

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === caseId) ?? null,
    [cases, caseId],
  );

  const inquiry = useInquiryPreview(caseId, selectedIds);
  const letter = inquiry.data ?? null;

  const handleCaseChange = (value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value === MANUAL_CASE) {
      appliedParam.current = null;
      setCaseId(null);
      setManualSelection(null);
      next.delete("case");
      setSearchParams(next, { replace: true });
      return;
    }
    const found = cases.find((item) => item.id === value);
    appliedParam.current = value;
    setCaseId(value);
    setManualSelection(null);
    if (found) setText(found.subject);
    next.set("case", value);
    setSearchParams(next, { replace: true });
  };

  const handleTextChange = (value: string) => {
    setText(value);
    setManualSelection(null);
  };

  const handleCopy = async () => {
    if (!letter) return;
    const copied = await copyText(letter.body);
    if (copied) toast.success(TEXT.copied);
    else toast.error(TEXT.copyFailed);
  };

  const handleDownload = () => {
    if (!letter || !selectedCase) return;
    downloadText(inquiryFileName(selectedCase.case_number), letter.body);
  };

  const allSelected = isAllSelected(selectedIds, suggestions);
  const hasText = text.trim().length >= MIN_TEXT_LENGTH;

  return (
    <div>
      <PageHeader title={TEXT.title} description={TEXT.description} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Treść wniosku</CardTitle>
              <CardDescription>{TEXT.caseHint}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sprawa">{TEXT.caseLabel}</Label>
                {casesQuery.isError ? (
                  <ErrorState error={casesQuery.error} onRetry={() => void casesQuery.refetch()} />
                ) : (
                  <Select
                    value={caseId ?? MANUAL_CASE}
                    onValueChange={handleCaseChange}
                    disabled={casesQuery.isLoading}
                  >
                    <SelectTrigger id="sprawa">
                      <SelectValue placeholder={TEXT.casePlaceholder} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={MANUAL_CASE}>{TEXT.caseManual}</SelectItem>
                      {cases.map((item) => (
                        <SelectItem key={item.id} value={item.id}>
                          {item.case_number} — {item.subject}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              {selectedCase ? (
                <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm">
                  <span className="font-medium">{selectedCase.case_number}</span>
                  <span className="text-muted-foreground">
                    termin {formatShortDate(selectedCase.deadline)}
                  </span>
                  <StatusBadge status={selectedCase.status} />
                  <UrgencyBadge
                    urgency={selectedCase.urgency}
                    days={selectedCase.days_remaining}
                  />
                </div>
              ) : null}

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <Label htmlFor="tresc">{TEXT.textLabel}</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleTextChange("")}
                    disabled={!text}
                  >
                    {TEXT.clearText}
                  </Button>
                </div>
                <Textarea
                  id="tresc"
                  value={text}
                  onChange={(event) => handleTextChange(event.target.value)}
                  placeholder={TEXT.textPlaceholder}
                  rows={5}
                />
                <p className="text-xs text-muted-foreground">{TEXT.textHint}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
              <div className="space-y-1">
                <CardTitle className="text-base">{TEXT.suggestionsTitle}</CardTitle>
                <CardDescription>{TEXT.suggestionsDescription}</CardDescription>
              </div>
              {suggestions.length > 0 ? (
                <div className="flex shrink-0 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setManualSelection(
                        allSelected ? [] : suggestions.map((item) => item.department_id),
                      )
                    }
                  >
                    {allSelected ? TEXT.clearSelection : TEXT.selectAll}
                  </Button>
                </div>
              ) : null}
            </CardHeader>
            <CardContent>
              {!hasText ? (
                <EmptyState title={TEXT.suggestionsEmpty} />
              ) : suggestionsQuery.isLoading ? (
                <LoadingState rows={3} />
              ) : suggestionsQuery.isError ? (
                <ErrorState
                  error={suggestionsQuery.error}
                  onRetry={() => void suggestionsQuery.refetch()}
                />
              ) : suggestions.length === 0 ? (
                <EmptyState
                  title={TEXT.suggestionsEmpty}
                  description={TEXT.suggestionsFailed}
                />
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-muted-foreground">
                    {TEXT.selectedCount(selectedIds.length)}
                  </p>
                  <ul className="space-y-2">
                    {suggestions.map((suggestion) => (
                      <SuggestionRow
                        key={suggestion.department_id}
                        suggestion={suggestion}
                        kind={kindById.get(suggestion.department_id)}
                        checked={selectedIds.includes(suggestion.department_id)}
                        onToggle={() =>
                          setManualSelection(toggleId(selectedIds, suggestion.department_id))
                        }
                      />
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:sticky lg:top-6 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-4 w-4" />
                {TEXT.previewTitle}
              </CardTitle>
              <CardDescription>{TEXT.previewDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!caseId ? (
                <EmptyState title={TEXT.previewNoCase} />
              ) : selectedIds.length === 0 ? (
                <EmptyState title={TEXT.previewNoSelection} />
              ) : inquiry.isLoading ? (
                <LoadingState rows={4} />
              ) : inquiry.isError ? (
                <ErrorState
                  error={inquiry.error}
                  onRetry={() => void inquiry.refetch()}
                />
              ) : letter ? (
                <>
                  <div className="space-y-2">
                    <p className="text-sm font-medium">{letter.title}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {letter.addressees.map((name) => (
                        <Badge key={name} variant="outline" className="font-normal">
                          {name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Separator />
                  <ScrollArea className="h-[26rem] rounded-md border bg-muted/30">
                    <pre className="whitespace-pre-wrap break-words p-3 font-sans text-sm leading-relaxed">
                      {letter.body}
                    </pre>
                  </ScrollArea>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={() => void handleCopy()}>
                      <Copy className="h-4 w-4" />
                      {TEXT.copy}
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDownload}>
                      <Download className="h-4 w-4" />
                      {TEXT.download}
                    </Button>
                  </div>
                  <Separator />
                  <Button asChild variant="secondary" size="sm" className="w-full">
                    <Link to={`/odpowiedzi?case=${caseId}`}>
                      <ArrowRight className="h-4 w-4" />
                      {TEXT.goToDraft}
                    </Link>
                  </Button>
                  <p className="text-xs text-muted-foreground">{TEXT.goToDraftHint}</p>
                </>
              ) : (
                <EmptyState title={TEXT.previewNoSelection} />
              )}
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Network className="h-4 w-4" />
                Jak dobierane są komórki
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>
                Dopasowanie uwzględnia polską odmianę, więc „dróg” i „droga” to to
                samo słowo.
              </p>
              <p>
                Frazy wielowyrazowe ważą więcej niż pojedyncze słowa, a słowa
                wspólne dla wielu komórek — mniej.
              </p>
              <p>
                Komórka, której słowa kluczowe pokrywają tylko wycinek zapytania,
                spada w rankingu.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
