import { FileText, Loader2, RefreshCw } from "lucide-react";

import { ErrorState, LoadingState } from "@/components/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  formatBytes,
  splitPages,
  useDocument,
  useDocumentChunks,
  type DocumentKind,
} from "@/features/ingest/api";
import { KIND_LABEL, STATUS_CLASS, STATUS_LABEL, TEXT } from "@/features/ingest/i18n";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

type PreviewDialogProps = {
  documentId: string | null;
  onClose: () => void;
  onReindex: (documentId: string) => void;
  reindexing: boolean;
};

export function PreviewDialog({
  documentId,
  onClose,
  onReindex,
  reindexing,
}: PreviewDialogProps) {
  const detail = useDocument(documentId);
  const chunks = useDocumentChunks(documentId);
  const pages = detail.data ? splitPages(detail.data.text) : [];
  const document = detail.data;

  return (
    <Dialog
      open={Boolean(documentId)}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 pr-8">
            <FileText className="h-4 w-4 shrink-0" />
            <span className="truncate">{document?.filename ?? TEXT.previewTitle}</span>
          </DialogTitle>
          <DialogDescription asChild>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {document ? (
                <>
                  <Badge variant="outline">
                    {KIND_LABEL[document.kind as DocumentKind] ?? document.kind}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(STATUS_CLASS[document.status])}
                  >
                    {STATUS_LABEL[document.status]}
                  </Badge>
                  <span>{formatBytes(document.size_bytes)}</span>
                  <span>·</span>
                  <span>{TEXT.pagesLabel(document.page_count)}</span>
                  <span>·</span>
                  <span>{TEXT.chunksLabel(document.chunk_count)}</span>
                  <span>·</span>
                  <span>{formatDateTime(document.created_at)}</span>
                </>
              ) : (
                <span>{TEXT.previewLoading}</span>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>

        {document?.error ? (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {document.error}
          </p>
        ) : null}

        {detail.isLoading ? (
          <LoadingState rows={4} />
        ) : detail.isError ? (
          <ErrorState error={detail.error} onRetry={() => void detail.refetch()} />
        ) : (
          <Tabs defaultValue="text" className="min-h-0">
            <TabsList>
              <TabsTrigger value="text">{TEXT.previewText}</TabsTrigger>
              <TabsTrigger value="chunks">
                {TEXT.previewChunks}
                {chunks.data ? ` (${chunks.data.length})` : ""}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="text">
              <ScrollArea className="h-[55vh] rounded-md border p-3">
                {pages.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{TEXT.previewNoText}</p>
                ) : (
                  <div className="space-y-4">
                    {pages.map((page, index) => (
                      <section key={index} className="space-y-1">
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          {TEXT.previewPage} {index + 1}
                        </h3>
                        {page ? (
                          <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">
                            {page}
                          </pre>
                        ) : (
                          <p className="text-sm text-muted-foreground">
                            {TEXT.previewEmptyPage}
                          </p>
                        )}
                      </section>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="chunks">
              <ScrollArea className="h-[55vh] rounded-md border p-3">
                {chunks.isLoading ? (
                  <LoadingState rows={3} />
                ) : chunks.isError ? (
                  <ErrorState error={chunks.error} onRetry={() => void chunks.refetch()} />
                ) : (chunks.data ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">{TEXT.previewNoChunks}</p>
                ) : (
                  <ol className="space-y-3">
                    {(chunks.data ?? []).map((chunk) => (
                      <li key={chunk.id} className="rounded-md border bg-muted/30 p-3">
                        <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant="secondary">#{chunk.index + 1}</Badge>
                          {chunk.page !== null ? (
                            <span>
                              {TEXT.previewPage} {chunk.page}
                            </span>
                          ) : null}
                          {chunk.section ? (
                            <span className="truncate">
                              {TEXT.previewSection}: {chunk.section}
                            </span>
                          ) : null}
                          <span className="ml-auto tabular-nums">
                            {chunk.text.length} znaków
                          </span>
                        </div>
                        <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">
                          {chunk.text}
                        </pre>
                      </li>
                    ))}
                  </ol>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            {TEXT.previewClose}
          </Button>
          <Button
            type="button"
            disabled={!documentId || reindexing}
            onClick={() => {
              if (documentId) onReindex(documentId);
            }}
          >
            {reindexing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {TEXT.actionReindex}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
