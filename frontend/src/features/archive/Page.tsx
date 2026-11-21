import { Search, Sparkles, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { findFeature } from "@/app/registry";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ArchiveCaseSheet } from "@/features/archive/ArchiveCaseSheet";
import { useSimilarCases } from "@/features/archive/api";
import {
  LIMIT_OPTIONS,
  MAX_QUERY_CHARS,
  TEXT,
  YEAR_OPTIONS,
} from "@/features/archive/i18n";
import {
  SCORE_BAR_CLASS,
  SCORE_TEXT_CLASS,
  formatScore,
  scorePercent,
  scoreTone,
  sortByScore,
} from "@/features/archive/score";
import type { SimilarCase } from "@/lib/types";
import { cn } from "@/lib/utils";

const ALL_YEARS = "all";

async function copyToClipboard(value: string): Promise<boolean> {
  try {
    if (!navigator.clipboard) return false;
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}

function MatchedTerms({ terms }: { terms: string[] }) {
  if (terms.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">{TEXT.noMatchedTerms}</p>
    );
  }
  return (
    <ul className="flex flex-wrap gap-1" aria-label={TEXT.matchedTermsLabel}>
      {terms.map((term) => (
        <li key={term}>
          <Badge variant="secondary" className="font-normal">
            {term}
          </Badge>
        </li>
      ))}
    </ul>
  );
}

function ResultCard({
  item,
  onOpen,
  onUse,
}: {
  item: SimilarCase;
  onOpen: (archiveId: string) => void;
  onUse: (archiveId: string, caseNumber: string) => void;
}) {
  const tone = scoreTone(item.score);
  return (
    <li className="rounded-lg border p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 space-y-1">
          <p className="font-mono text-xs text-muted-foreground">{item.case_number}</p>
          <h3 className="font-medium leading-snug">{item.subject}</h3>
          <p className="text-xs text-muted-foreground">{TEXT.yearLabel(item.year)}</p>
        </div>
        <div className="w-32 shrink-0 space-y-1">
          <p
            className={cn(
              "text-right text-sm font-semibold tabular-nums",
              SCORE_TEXT_CLASS[tone],
            )}
          >
            {formatScore(item.score)}
          </p>
          <Progress
            value={scorePercent(item.score)}
            className={SCORE_BAR_CLASS[tone]}
            aria-label={`${TEXT.scoreLabel}: ${formatScore(item.score)}`}
          />
        </div>
      </div>

      <div className="mt-3">
        <MatchedTerms terms={item.matched_terms} />
      </div>

      <div className="mt-3 space-y-2">
        <div>
          <p className="text-xs font-medium text-muted-foreground">
            {TEXT.requestExcerptLabel}
          </p>
          <p className="text-sm leading-relaxed">{item.snippet}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground">
            {TEXT.responseExcerptLabel}
          </p>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {item.response_excerpt}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => onOpen(item.archive_id)}>
          {TEXT.details}
        </Button>
        <Button
          size="sm"
          onClick={() => onUse(item.archive_id, item.case_number)}
        >
          <Sparkles className="mr-1 h-4 w-4" />
          {TEXT.useInResponse}
        </Button>
      </div>
    </li>
  );
}

export default function ArchivePage() {
  const navigate = useNavigate();
  const search = useSimilarCases();

  const [text, setText] = useState("");
  const [limit, setLimit] = useState<string>("5");
  const [yearFrom, setYearFrom] = useState<string>(ALL_YEARS);
  const [results, setResults] = useState<SimilarCase[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const sorted = useMemo(() => (results ? sortByScore(results) : null), [results]);
  const remaining = MAX_QUERY_CHARS - text.length;

  const runSearch = () => {
    const trimmed = text.trim();
    if (!trimmed) {
      toast.error(TEXT.emptyQuery);
      return;
    }
    search.mutate(
      {
        text: trimmed,
        k: Number(limit),
        year_from: yearFrom === ALL_YEARS ? undefined : Number(yearFrom),
      },
      {
        onSuccess: (data) => setResults(data),
        onError: (error) =>
          toast.error(error instanceof Error ? error.message : TEXT.searchFailed),
      },
    );
  };

  const clearQuery = () => {
    setText("");
    setResults(null);
  };

  const sendToDrafting = async (caseNumber: string) => {
    const copied = await copyToClipboard(caseNumber);
    if (copied) {
      toast.success(TEXT.copied(caseNumber));
    } else {
      toast.info(TEXT.copyFailed(caseNumber));
    }

    const drafting = findFeature("drafting");
    if (drafting) {
      // Numer sprawy archiwalnej nie jest identyfikatorem sprawy w kalendarzu,
      // więc otwieramy generator bez wybranej sprawy — urzędnik wybiera ją sam,
      // a numer sprawy archiwalnej ma już w schowku.
      navigate(`/${drafting.path}`);
    } else {
      toast.info(TEXT.noDraftingScreen(caseNumber));
    }
  };

  return (
    <div>
      <PageHeader title={TEXT.title} description={TEXT.description} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
        <Card>
          <CardHeader>
            <CardTitle>{TEXT.queryTitle}</CardTitle>
            <CardDescription>{TEXT.queryDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="archive-query">{TEXT.queryLabel}</Label>
              <Textarea
                id="archive-query"
                value={text}
                maxLength={MAX_QUERY_CHARS}
                rows={7}
                placeholder={TEXT.queryPlaceholder}
                onChange={(event) => setText(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                    event.preventDefault();
                    runSearch();
                  }
                }}
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs text-muted-foreground">{TEXT.queryHint}</p>
                <p
                  className={cn(
                    "text-xs tabular-nums text-muted-foreground",
                    remaining < 200 && "text-amber-700 dark:text-amber-300",
                  )}
                  aria-live="polite"
                >
                  {TEXT.charCounter(text.length, MAX_QUERY_CHARS)}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={runSearch} disabled={search.isPending}>
                <Search className="mr-1 h-4 w-4" />
                {search.isPending ? TEXT.searching : TEXT.search}
              </Button>
              <Button
                variant="outline"
                onClick={clearQuery}
                disabled={search.isPending || (text === "" && results === null)}
              >
                <X className="mr-1 h-4 w-4" />
                {TEXT.clear}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">{TEXT.optionsTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="archive-limit">{TEXT.limitLabel}</Label>
              <Select value={limit} onValueChange={setLimit}>
                <SelectTrigger id="archive-limit">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LIMIT_OPTIONS.map((option) => (
                    <SelectItem key={option} value={String(option)}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label htmlFor="archive-year">{TEXT.yearFromLabel}</Label>
              <Select value={yearFrom} onValueChange={setYearFrom}>
                <SelectTrigger id="archive-year">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_YEARS}>{TEXT.yearAny}</SelectItem>
                  {YEAR_OPTIONS.map((year) => (
                    <SelectItem key={year} value={String(year)}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      <section className="mt-8" aria-live="polite">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-semibold">{TEXT.resultsTitle}</h2>
          {sorted && sorted.length > 0 ? (
            <p className="text-xs text-muted-foreground">
              {TEXT.resultsCount(sorted.length)} · {TEXT.resultsHint}
            </p>
          ) : null}
        </div>

        {search.isPending ? (
          <LoadingState rows={3} />
        ) : search.isError ? (
          <ErrorState error={search.error} onRetry={runSearch} />
        ) : sorted === null ? (
          <EmptyState
            title={TEXT.emptyTitle}
            description={TEXT.emptyDescription}
          />
        ) : sorted.length === 0 ? (
          <EmptyState
            title={TEXT.noResultsTitle}
            description={TEXT.noResultsDescription}
          />
        ) : (
          <ul className="space-y-3">
            {sorted.map((item) => (
              <ResultCard
                key={item.archive_id}
                item={item}
                onOpen={setSelectedId}
                onUse={(_archiveId, caseNumber) => {
                  void sendToDrafting(caseNumber);
                }}
              />
            ))}
          </ul>
        )}
      </section>

      <ArchiveCaseSheet
        archiveId={selectedId}
        onClose={() => setSelectedId(null)}
        onUseInResponse={(_archiveId, caseNumber) => {
          void sendToDrafting(caseNumber);
        }}
      />
    </div>
  );
}
