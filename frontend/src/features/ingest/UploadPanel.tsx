import { FileUp, Loader2, Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import {
  errorMessage,
  formatBytes,
  useUploadDocument,
  type DocumentKind,
} from "@/features/ingest/api";
import { KIND_OPTIONS, TEXT } from "@/features/ingest/i18n";
import { useCases } from "@/lib/hooks";
import { cn } from "@/lib/utils";

const ACCEPTED = ".pdf,.docx,.txt,.md";

export function UploadPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<DocumentKind>("wniosek");
  const [caseId, setCaseId] = useState("none");
  const [title, setTitle] = useState("");
  const [progress, setProgress] = useState(0);
  const [dragging, setDragging] = useState(false);

  const cases = useCases();
  const upload = useUploadDocument();

  function pick(next: File | null) {
    setFile(next);
    setProgress(0);
    // pozwala wybrać ten sam plik ponownie po błędzie
    if (inputRef.current) inputRef.current.value = "";
  }

  function submit() {
    if (!file) return;
    setProgress(0);
    upload.mutate(
      {
        file,
        kind,
        caseId: caseId === "none" ? undefined : caseId,
        title: title.trim() || undefined,
        onProgress: setProgress,
      },
      {
        onSuccess: (document) => {
          if (document.status === "failed") {
            toast.warning(TEXT.uploadParseFailed, {
              description: document.error ?? undefined,
            });
          } else {
            toast.success(TEXT.uploadSuccess, {
              description: `${document.filename} — ${TEXT.chunksLabel(document.chunk_count)}`,
            });
          }
          pick(null);
          setTitle("");
        },
        onError: (error) => {
          toast.error(TEXT.uploadFailed, { description: errorMessage(error) });
        },
      },
    );
  }

  const busy = upload.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileUp className="h-4 w-4" />
          {TEXT.uploadTitle}
        </CardTitle>
        <CardDescription>{TEXT.uploadFormats}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          role="button"
          tabIndex={0}
          aria-label={TEXT.uploadHint}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            const dropped = event.dataTransfer.files?.[0];
            if (dropped) pick(dropped);
          }}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors",
            dragging
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/60 hover:bg-muted/40",
            busy && "pointer-events-none opacity-60",
          )}
        >
          <Upload className="h-6 w-6 text-muted-foreground" />
          <p className="text-sm font-medium">{TEXT.uploadHint}</p>
          <p className="text-xs text-muted-foreground">{TEXT.uploadFormats}</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(event) => pick(event.target.files?.[0] ?? null)}
          />
        </div>

        {file ? (
          <div className="flex items-center justify-between gap-3 rounded-md border bg-muted/40 px-3 py-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label={TEXT.uploadClear}
              disabled={busy}
              onClick={() => pick(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="upload-kind">{TEXT.uploadKind}</Label>
            <Select
              value={kind}
              onValueChange={(value) => setKind(value as DocumentKind)}
              disabled={busy}
            >
              <SelectTrigger id="upload-kind">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {KIND_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label htmlFor="upload-case">{TEXT.uploadCase}</Label>
            <Select value={caseId} onValueChange={setCaseId} disabled={busy}>
              <SelectTrigger id="upload-case">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">{TEXT.uploadCaseNone}</SelectItem>
                {(cases.data ?? []).map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.case_number} — {item.subject.slice(0, 48)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-1">
          <Label htmlFor="upload-title">{TEXT.uploadTitleField}</Label>
          <Input
            id="upload-title"
            value={title}
            placeholder={TEXT.uploadTitlePlaceholder}
            disabled={busy}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>

        {busy ? (
          <div className="space-y-1" aria-live="polite">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                {progress < 100 ? TEXT.uploadProgress : TEXT.uploadProcessing}
              </span>
              <span className="tabular-nums">{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        ) : null}

        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={!file || busy}
            onClick={() => pick(null)}
          >
            {TEXT.uploadClear}
          </Button>
          <Button type="button" disabled={!file || busy} onClick={submit}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {TEXT.uploadSubmit}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
