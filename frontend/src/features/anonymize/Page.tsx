import {
  Check,
  CheckCheck,
  Copy,
  Eraser,
  Plus,
  ScanSearch,
  ShieldCheck,
  Trash2,
  Undo2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { apiErrorMessage } from "@/components/errorMessages";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import {
  useAnonymizerMetrics,
  useApplyAnonymization,
  useDetectSpans,
} from "./api";
import {
  CATEGORY_ORDER,
  EXAMPLE_TEXT,
  SOURCE_LABELS,
  TEXT,
  categoryLabel,
  categoryStyle,
} from "./i18n";
import {
  acceptedOnly,
  buildSegments,
  toggleAcceptance,
  withSpan,
  withoutSpan,
  type ReviewSpan,
} from "./segments";

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function MetricTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1 rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold tabular-nums">{percent(value)}</p>
      <Progress value={value * 100} aria-label={label} />
    </div>
  );
}

export default function AnonymizePage() {
  const [text, setText] = useState("");
  const [spans, setSpans] = useState<ReviewSpan[]>([]);
  const [placeholder, setPlaceholder] = useState("[USUNIĘTO]");
  const [result, setResult] = useState<string | null>(null);
  const [manualCategory, setManualCategory] = useState("imie_nazwisko");
  const [stale, setStale] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const detect = useDetectSpans();
  const apply = useApplyAnonymization();
  const metrics = useAnonymizerMetrics();

  const segments = useMemo(() => buildSegments(text, spans), [text, spans]);
  const acceptedCount = useMemo(() => acceptedOnly(spans).length, [spans]);

  // Pole rośnie z treścią, więc nigdy nie pojawia się w nim pasek przewijania —
  // dzięki temu warstwa podświetleń pokrywa się z tekstem co do piksela.
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.max(textarea.scrollHeight, 256)}px`;
  }, [text]);

  const handleTextChange = (value: string) => {
    setText(value);
    setResult(null);
    if (spans.length > 0) {
      setSpans([]);
      setStale(true);
    }
  };

  const handleDetect = () => {
    if (!text.trim()) {
      toast.error(TEXT.emptyText);
      return;
    }
    detect.mutate(
      { text },
      {
        onSuccess: (found) => {
          setSpans(found.map((span) => ({ ...span, accepted: false })));
          setResult(null);
          setStale(false);
        },
        onError: (error) => {
          toast.error(TEXT.detectFailed, {
            description: apiErrorMessage(error),
          });
        },
      },
    );
  };

  const handleApply = () => {
    if (!text.trim()) {
      toast.error(TEXT.emptyText);
      return;
    }
    const accepted = acceptedOnly(spans);
    if (accepted.length === 0) {
      toast.error(TEXT.nothingAccepted);
      return;
    }
    apply.mutate(
      { text, spans: accepted, placeholder },
      {
        onSuccess: (data) => {
          setResult(data.text);
          toast.success(`${TEXT.removed}: ${data.removed_count}`);
        },
        onError: (error) => {
          toast.error(TEXT.applyFailed, {
            description: apiErrorMessage(error),
          });
        },
      },
    );
  };

  const handleAddSelection = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (start === end) {
      toast.error(TEXT.noSelection);
      return;
    }
    setSpans((previous) =>
      withSpan(previous, {
        start,
        end,
        text: text.slice(start, end),
        category: manualCategory,
        confidence: 1,
        source: "llm",
        accepted: true,
      }),
    );
    setResult(null);
    setStale(false);
  };

  const handleRemove = (span: ReviewSpan) => {
    setSpans((previous) => withoutSpan(previous, span));
    setResult(null);
  };

  const handleToggleAccept = (span: ReviewSpan) => {
    setSpans((previous) => toggleAcceptance(previous, span));
    setResult(null);
  };

  const handleAcceptAll = () => {
    setSpans((previous) =>
      previous.map((item) => ({ ...item, accepted: true })),
    );
    setResult(null);
  };

  const handleRejectAll = () => {
    setSpans([]);
    setResult(null);
  };

  const handleCopy = async () => {
    if (result === null) return;
    try {
      await navigator.clipboard.writeText(result);
      toast.success(TEXT.copied);
    } catch {
      toast.error(TEXT.copyFailed);
    }
  };

  const handleClear = () => {
    setText("");
    setSpans([]);
    setResult(null);
    setStale(false);
  };

  const handleExample = () => {
    setText(EXAMPLE_TEXT);
    setSpans([]);
    setResult(null);
    setStale(false);
  };

  const categories = useMemo(() => {
    const data = metrics.data?.per_category ?? {};
    return Object.keys(data).sort((a, b) => {
      const left = CATEGORY_ORDER.indexOf(a);
      const right = CATEGORY_ORDER.indexOf(b);
      return (left === -1 ? 99 : left) - (right === -1 ? 99 : right);
    });
  }, [metrics.data]);

  return (
    <div>
      <PageHeader
        title={TEXT.title}
        description={TEXT.description}
        actions={
          <>
            <Button variant="outline" onClick={handleExample}>
              <ShieldCheck />
              {TEXT.example}
            </Button>
            <Button variant="ghost" onClick={handleClear}>
              <Eraser />
              {TEXT.clear}
            </Button>
          </>
        }
      />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>{TEXT.inputTitle}</CardTitle>
              <CardDescription>{TEXT.inputDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="relative">
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-words rounded-md border border-transparent px-3 py-2 font-mono text-sm leading-6 text-transparent"
                >
                  {segments.map((segment, index) =>
                    segment.span ? (
                      <mark
                        key={index}
                        className={cn(
                          "rounded-sm text-transparent",
                          segment.span.accepted
                            ? categoryStyle(segment.span.category).mark
                            : "bg-slate-400/25",
                        )}
                      >
                        {segment.text}
                      </mark>
                    ) : (
                      <span key={index}>{segment.text}</span>
                    ),
                  )}
                  {"\u200b"}
                </div>
                <Textarea
                  ref={textareaRef}
                  value={text}
                  onChange={(event) => handleTextChange(event.target.value)}
                  spellCheck={false}
                  aria-label={TEXT.inputTitle}
                  placeholder="Wklej treść pisma…"
                  className="relative min-h-64 resize-none overflow-hidden bg-transparent font-mono text-sm leading-6"
                />
              </div>

              <div className="flex flex-wrap items-end gap-2">
                <Button onClick={handleDetect} disabled={detect.isPending}>
                  <ScanSearch />
                  {detect.isPending ? TEXT.detecting : TEXT.detect}
                </Button>

                <div className="space-y-1">
                  <Label htmlFor="manual-category">{TEXT.categoryLabel}</Label>
                  <Select value={manualCategory} onValueChange={setManualCategory}>
                    <SelectTrigger id="manual-category" className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORY_ORDER.map((category) => (
                        <SelectItem key={category} value={category}>
                          {categoryLabel(category)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button variant="outline" onClick={handleAddSelection}>
                  <Plus />
                  {TEXT.addSelection}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {TEXT.addSelectionHint}
              </p>

              <Separator />

              <div className="flex flex-wrap items-end gap-2">
                <div className="space-y-1">
                  <Label htmlFor="placeholder">{TEXT.placeholderLabel}</Label>
                  <Input
                    id="placeholder"
                    value={placeholder}
                    onChange={(event) => setPlaceholder(event.target.value)}
                    className="w-48 font-mono"
                  />
                </div>
                <Button
                  onClick={handleApply}
                  disabled={apply.isPending || acceptedCount === 0}
                >
                  {apply.isPending ? TEXT.applying : TEXT.apply}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {TEXT.placeholderHint}
              </p>
              {spans.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {acceptedCount} z {spans.length} {TEXT.acceptedSummary}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
              <div className="space-y-1">
                <CardTitle>{TEXT.resultTitle}</CardTitle>
                <CardDescription>{TEXT.resultDescription}</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                disabled={result === null}
              >
                <Copy />
                {TEXT.copy}
              </Button>
            </CardHeader>
            <CardContent>
              {result === null ? (
                <EmptyState
                  title="Brak podglądu"
                  description="Zaakceptuj zaznaczenia i uruchom anonimizację, żeby zobaczyć wynik."
                />
              ) : (
                <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md border bg-muted/40 p-3 font-mono text-sm">
                  {result}
                </pre>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
              <div className="space-y-1">
                <CardTitle>
                  {TEXT.spansTitle}
                  {spans.length > 0 ? ` (${acceptedCount}/${spans.length})` : ""}
                </CardTitle>
                <CardDescription>
                  {stale
                    ? TEXT.spansStale
                    : spans.length > 0
                      ? TEXT.pendingHint
                      : TEXT.addSelectionHint}
                </CardDescription>
              </div>
              {spans.length > 0 && (
                <div className="flex shrink-0 gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAcceptAll}
                    disabled={acceptedCount === spans.length}
                  >
                    <CheckCheck />
                    {TEXT.acceptAll}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleRejectAll}>
                    <X />
                    {TEXT.rejectAll}
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              {spans.length === 0 ? (
                <EmptyState title={TEXT.spansEmpty} />
              ) : (
                <ul className="max-h-[26rem] space-y-2 overflow-auto pr-1">
                  {spans.map((span) => (
                    <li
                      key={`${span.start}-${span.end}-${span.category}`}
                      className={cn(
                        "flex items-start justify-between gap-2 rounded-md border p-2",
                        !span.accepted && "border-dashed bg-muted/30",
                      )}
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-1">
                          <Badge
                            variant="outline"
                            className={
                              span.accepted
                                ? categoryStyle(span.category).badge
                                : "border-slate-400/40 bg-slate-400/10 text-slate-600 dark:text-slate-400"
                            }
                          >
                            {categoryLabel(span.category)}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {SOURCE_LABELS[span.source] ?? span.source} ·{" "}
                            {percent(span.confidence)}
                          </span>
                        </div>
                        <p className="break-words font-mono text-xs">
                          {span.text}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleToggleAccept(span)}
                          aria-label={
                            span.accepted ? TEXT.unaccept : TEXT.accept
                          }
                          title={span.accepted ? TEXT.unaccept : TEXT.accept}
                        >
                          {span.accepted ? <Undo2 /> : <Check />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemove(span)}
                          aria-label={`${TEXT.remove}: ${span.text}`}
                        >
                          <Trash2 />
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{TEXT.metricsTitle}</CardTitle>
              <CardDescription>{TEXT.metricsDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {metrics.isLoading ? (
                <LoadingState rows={2} />
              ) : metrics.isError ? (
                <ErrorState
                  error={metrics.error}
                  onRetry={() => void metrics.refetch()}
                />
              ) : metrics.data ? (
                <>
                  <div className="grid grid-cols-3 gap-2">
                    <MetricTile
                      label={TEXT.precision}
                      value={metrics.data.precision}
                    />
                    <MetricTile label={TEXT.recall} value={metrics.data.recall} />
                    <MetricTile label={TEXT.f1} value={metrics.data.f1} />
                  </div>

                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{TEXT.category}</TableHead>
                        <TableHead className="text-right">
                          {TEXT.precision}
                        </TableHead>
                        <TableHead className="text-right">
                          {TEXT.recall}
                        </TableHead>
                        <TableHead className="text-right">
                          {TEXT.support}
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {categories.map((category) => {
                        const row = metrics.data.per_category[category];
                        return (
                          <TableRow key={category}>
                            <TableCell className="py-1.5">
                              <Badge
                                variant="outline"
                                className={categoryStyle(category).badge}
                              >
                                {categoryLabel(category)}
                              </Badge>
                            </TableCell>
                            <TableCell className="py-1.5 text-right tabular-nums">
                              {percent(row.precision)}
                            </TableCell>
                            <TableCell className="py-1.5 text-right tabular-nums">
                              {percent(row.recall)}
                            </TableCell>
                            <TableCell className="py-1.5 text-right tabular-nums">
                              {row.support}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </>
              ) : (
                <EmptyState title={TEXT.metricsUnavailable} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
