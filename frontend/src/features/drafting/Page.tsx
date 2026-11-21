import { Download, FileText, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CitationPanel } from "@/features/drafting/CitationPanel";
import { DraftEditor, type DraftEditorHandle } from "@/features/drafting/Editor";
import { UnsupportedPanel } from "@/features/drafting/UnsupportedPanel";
import {
  downloadBlob,
  errorMessage,
  isMissingDraft,
  useCreateDraft,
  useDraft,
  useExportDraft,
  useSaveDraft,
  type DraftFormat,
} from "@/features/drafting/api";
import { TEXT } from "@/features/drafting/i18n";
import { sectionForClaim } from "@/features/drafting/markdown";
import { formatDateTime } from "@/lib/format";
import { useCases } from "@/lib/hooks";

const AUTOSAVE_MS = 2000;

type SaveState = "idle" | "saving" | "error";

export default function DraftingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const caseId = searchParams.get("case");
  const [body, setBody] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [activeRef, setActiveRef] = useState<number | null>(null);
  const [anonymized, setAnonymized] = useState(false);
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);

  const editorRef = useRef<DraftEditorHandle>(null);
  const loadedDraftId = useRef<string | null>(null);
  const latestBody = useRef(body);

  const cases = useCases({ sort: "deadline_asc" });
  const draft = useDraft(caseId);
  const create = useCreateDraft();
  const save = useSaveDraft();
  const exportDraft = useExportDraft();
  const saveDraft = save.mutate;

  const draftId = draft.data?.id ?? null;
  const citations = useMemo(() => draft.data?.citations ?? [], [draft.data]);
  const unsupported = useMemo(() => draft.data?.unsupported ?? [], [draft.data]);

  useEffect(() => {
    latestBody.current = body;
  }, [body]);

  useEffect(() => {
    setBody("");
    setDirty(false);
    setSaveState("idle");
    setActiveRef(null);
    loadedDraftId.current = null;
  }, [caseId]);

  useEffect(() => {
    const data = draft.data;
    if (!data) return;
    if (loadedDraftId.current === data.id) return;
    loadedDraftId.current = data.id;
    setBody(data.body);
    setDirty(false);
    setSaveState("idle");
  }, [draft.data]);

  const persist = useCallback(
    (nextBody: string) => {
      if (!draftId) return;
      setSaveState("saving");
      saveDraft(
        { draftId, body: nextBody },
        {
          onSuccess: () => {
            if (latestBody.current === nextBody) {
              setDirty(false);
              setSaveState("idle");
            }
          },
          onError: (error) => {
            setSaveState("error");
            toast.error(TEXT.saveError, { description: errorMessage(error) });
          },
        },
      );
    },
    [draftId, saveDraft],
  );

  useEffect(() => {
    if (!dirty || !draftId) return;
    const timer = window.setTimeout(() => persist(body), AUTOSAVE_MS);
    return () => window.clearTimeout(timer);
  }, [body, dirty, draftId, persist]);

  const handleChange = useCallback((next: string) => {
    setBody(next);
    setDirty(true);
  }, []);

  const selectCase = useCallback(
    (value: string) => {
      const next = new URLSearchParams(searchParams);
      next.set("case", value);
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const runGenerate = useCallback(() => {
    if (!caseId) return;
    create.mutate(caseId, {
      onSuccess: (next) => {
        loadedDraftId.current = next.id;
        setBody(next.body);
        setDirty(false);
        setSaveState("idle");
        setActiveRef(null);
        toast.success(TEXT.generateSuccess, {
          description: TEXT.countLabel(next.citations.length),
        });
      },
      onError: (error) => {
        toast.error(TEXT.generateFailed, { description: errorMessage(error) });
      },
    });
  }, [caseId, create]);

  const handleGenerate = useCallback(() => {
    if (draft.data) {
      setConfirmRegenerate(true);
      return;
    }
    runGenerate();
  }, [draft.data, runGenerate]);

  const handleSelectCitation = useCallback((ref: number) => {
    setActiveRef(ref);
    const found = editorRef.current?.scrollToMarker(ref) ?? false;
    if (!found) {
      toast.info(TEXT.citationMissing);
    }
  }, []);

  const handleGoToSection = useCallback((section: string) => {
    const found = editorRef.current?.scrollToText(section) ?? false;
    if (!found) {
      toast.info(TEXT.unsupportedNoSection);
    }
  }, []);

  const handleExport = useCallback(
    (format: DraftFormat) => {
      if (!draftId) {
        toast.error(TEXT.exportMissing);
        return;
      }
      exportDraft.mutate(
        { draftId, format, anonymized },
        {
          onSuccess: ({ blob, filename }) => {
            downloadBlob(blob, filename);
            toast.success(TEXT.exportSuccess, { description: filename });
          },
          onError: (error) => {
            toast.error(TEXT.exportFailed, { description: errorMessage(error) });
          },
        },
      );
    },
    [anonymized, draftId, exportDraft],
  );

  const caseOptions = cases.data ?? [];
  const selectedCase = caseOptions.find((item) => item.id === caseId) ?? null;
  const generating = create.isPending;
  const exporting = exportDraft.isPending;
  const unsupportedItems = useMemo(
    () =>
      unsupported.map((claim) => ({
        claim,
        section: sectionForClaim(body, claim),
      })),
    [body, unsupported],
  );

  const saveLabel =
    saveState === "saving"
      ? TEXT.saveSaving
      : saveState === "error"
        ? TEXT.saveError
        : dirty
          ? TEXT.saveDirty
          : TEXT.saveSaved;

  return (
    <div className="space-y-4">
      <PageHeader title={TEXT.title} description={TEXT.description} />

      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1 space-y-1.5">
            <Label htmlFor="drafting-case">{TEXT.caseLabel}</Label>
            <Select
              value={caseId ?? ""}
              onValueChange={selectCase}
              disabled={cases.isLoading}
            >
              <SelectTrigger id="drafting-case" className="w-full">
                <SelectValue placeholder={TEXT.casePlaceholder} />
              </SelectTrigger>
              <SelectContent>
                {caseOptions.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    <span className="truncate">
                      {item.case_number} — {item.subject}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button onClick={handleGenerate} disabled={!caseId || generating}>
              {generating ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : draft.data ? (
                <RefreshCw className="mr-1.5 h-4 w-4" />
              ) : (
                <Sparkles className="mr-1.5 h-4 w-4" />
              )}
              {generating
                ? TEXT.generating
                : draft.data
                  ? TEXT.regenerate
                  : TEXT.generate}
            </Button>
          </div>
        </CardContent>
      </Card>

      {cases.isLoading ? <LoadingState rows={2} /> : null}
      {cases.isError ? (
        <ErrorState error={cases.error} onRetry={() => void cases.refetch()} />
      ) : null}

      {!caseId && !cases.isLoading && !cases.isError ? (
        <EmptyState
          title={TEXT.noCaseTitle}
          description={TEXT.noCaseDescription}
          action={
            caseOptions.length === 0 ? (
              <Badge variant="outline">{TEXT.caseEmpty}</Badge>
            ) : undefined
          }
        />
      ) : null}

      {caseId && draft.isLoading ? <LoadingState rows={4} /> : null}

      {caseId && draft.isError && !isMissingDraft(draft.error) ? (
        <ErrorState error={draft.error} onRetry={() => void draft.refetch()} />
      ) : null}

      {caseId && draft.isError && isMissingDraft(draft.error) ? (
        <EmptyState
          title={TEXT.noDraftTitle}
          description={TEXT.noDraftDescription}
          action={
            <Button onClick={runGenerate} disabled={generating}>
              {generating ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-1.5 h-4 w-4" />
              )}
              {generating ? TEXT.generating : TEXT.generate}
            </Button>
          }
        />
      ) : null}

      {draft.data ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-3">
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
                <div className="min-w-0">
                  <CardTitle className="truncate text-base">{draft.data.title}</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {selectedCase ? `${selectedCase.case_number} · ` : ""}
                    {TEXT.updatedAt}: {formatDateTime(draft.data.updated_at ?? draft.data.created_at)}
                  </p>
                </div>
                <span
                  className={
                    saveState === "error"
                      ? "shrink-0 text-xs font-medium text-destructive"
                      : "shrink-0 text-xs text-muted-foreground"
                  }
                  aria-live="polite"
                >
                  {saveLabel}
                </span>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-xs text-muted-foreground">{TEXT.editorHint}</p>
                <DraftEditor
                  ref={editorRef}
                  markdown={body}
                  onChange={handleChange}
                />
                {saveState === "error" ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => persist(latestBody.current)}
                  >
                    {TEXT.saveRetry}
                  </Button>
                ) : null}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-3">
            {unsupported.length > 0 ? (
              <Card className="border-amber-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    {TEXT.unsupportedTitle}
                    <Badge variant="outline" className="border-amber-300 text-amber-900">
                      {TEXT.unsupportedCount(unsupported.length)}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <UnsupportedPanel items={unsupportedItems} onGoTo={handleGoToSection} />
                </CardContent>
              </Card>
            ) : null}

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  {TEXT.citationsTitle}
                  <Badge variant="outline">{TEXT.countLabel(citations.length)}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CitationPanel
                  citations={citations}
                  activeRef={activeRef}
                  onSelect={handleSelectCitation}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">{TEXT.exportTitle}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-2">
                  <Checkbox
                    id="drafting-anonymized"
                    checked={anonymized}
                    onCheckedChange={(value) => setAnonymized(value === true)}
                  />
                  <div className="space-y-0.5">
                    <Label htmlFor="drafting-anonymized" className="text-sm font-medium">
                      {TEXT.exportAnonymized}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {TEXT.exportAnonymizedHint}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={exporting}
                    onClick={() => handleExport("docx")}
                  >
                    <Download className="mr-1.5 h-4 w-4" />
                    {TEXT.exportDocx}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={exporting}
                    onClick={() => handleExport("pdf")}
                  >
                    <Download className="mr-1.5 h-4 w-4" />
                    {TEXT.exportPdf}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={exporting}
                    onClick={() => handleExport("md")}
                  >
                    <FileText className="mr-1.5 h-4 w-4" />
                    {TEXT.exportMarkdown}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </aside>
        </div>
      ) : null}

      <AlertDialog open={confirmRegenerate} onOpenChange={setConfirmRegenerate}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{TEXT.regenerateTitle}</AlertDialogTitle>
            <AlertDialogDescription>{TEXT.regenerateDescription}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{TEXT.regenerateCancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmRegenerate(false);
                runGenerate();
              }}
            >
              {TEXT.regenerateConfirm}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
