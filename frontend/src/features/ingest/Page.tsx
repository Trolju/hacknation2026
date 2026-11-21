import type { ColumnDef } from "@tanstack/react-table";
import { Eye, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { DataTable } from "@/components/DataTable";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PreviewDialog } from "@/features/ingest/PreviewDialog";
import { UploadPanel } from "@/features/ingest/UploadPanel";
import {
  errorMessage,
  formatBytes,
  useDeleteDocument,
  useDocuments,
  useReindexDocument,
  type DocumentKind,
} from "@/features/ingest/api";
import {
  KIND_LABEL,
  KIND_OPTIONS,
  STATUS_CLASS,
  STATUS_LABEL,
  TEXT,
} from "@/features/ingest/i18n";
import { formatDateTime } from "@/lib/format";
import type { Document } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function IngestPage() {
  const [kind, setKind] = useState<DocumentKind | "all">("all");
  const [search, setSearch] = useState("");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);

  const documents = useDocuments({ kind: kind === "all" ? undefined : kind });
  const remove = useDeleteDocument();
  const reindex = useReindexDocument();

  const needle = search.trim().toLowerCase();
  const rows = (documents.data ?? []).filter((document) =>
    needle
      ? `${document.filename} ${document.title ?? ""}`.toLowerCase().includes(needle)
      : true,
  );

  function handleReindex(documentId: string) {
    reindex.mutate(documentId, {
      onSuccess: (document) => {
        if (document.status === "failed") {
          toast.warning(TEXT.uploadParseFailed, {
            description: document.error ?? undefined,
          });
          return;
        }
        toast.success(TEXT.reindexSuccess, {
          description: `${document.filename} — ${TEXT.chunksLabel(document.chunk_count)}`,
        });
      },
      onError: (error) => {
        toast.error(TEXT.reindexFailed, { description: errorMessage(error) });
      },
    });
  }

  function handleDelete() {
    if (!deleteTarget) return;
    const target = deleteTarget;
    remove.mutate(target.id, {
      onSuccess: () => {
        toast.success(TEXT.deleteSuccess, { description: target.filename });
        if (previewId === target.id) setPreviewId(null);
        setDeleteTarget(null);
      },
      onError: (error) => {
        toast.error(TEXT.deleteFailed, { description: errorMessage(error) });
        setDeleteTarget(null);
      },
    });
  }

  const columns: ColumnDef<Document, unknown>[] = [
    {
      accessorKey: "filename",
      header: TEXT.columnName,
      cell: ({ row }) => (
        <div className="min-w-0 max-w-xs">
          <p className="truncate font-medium">{row.original.filename}</p>
          {row.original.title && row.original.title !== row.original.filename ? (
            <p className="truncate text-xs text-muted-foreground">{row.original.title}</p>
          ) : null}
        </div>
      ),
    },
    {
      accessorKey: "kind",
      header: TEXT.columnKind,
      cell: ({ row }) => (
        <Badge variant="outline" className="whitespace-nowrap">
          {KIND_LABEL[row.original.kind as DocumentKind] ?? row.original.kind}
        </Badge>
      ),
    },
    {
      accessorKey: "size_bytes",
      header: TEXT.columnSize,
      cell: ({ row }) => (
        <span className="whitespace-nowrap tabular-nums">
          {formatBytes(row.original.size_bytes)}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: TEXT.columnStatus,
      cell: ({ row }) => (
        <Badge
          variant="outline"
          className={cn("whitespace-nowrap", STATUS_CLASS[row.original.status])}
          title={row.original.error ?? undefined}
        >
          {STATUS_LABEL[row.original.status]}
        </Badge>
      ),
    },
    {
      accessorKey: "chunk_count",
      header: TEXT.columnChunks,
      cell: ({ row }) => (
        <span className="tabular-nums">{row.original.chunk_count}</span>
      ),
    },
    {
      accessorKey: "created_at",
      header: TEXT.columnDate,
      cell: ({ row }) => (
        <span className="whitespace-nowrap">{formatDateTime(row.original.created_at)}</span>
      ),
    },
    {
      id: "actions",
      header: TEXT.columnActions,
      enableSorting: false,
      cell: ({ row }) => (
        <div
          className="flex justify-end gap-1"
          onClick={(event) => event.stopPropagation()}
        >
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={TEXT.actionPreview}
            title={TEXT.actionPreview}
            onClick={() => setPreviewId(row.original.id)}
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={TEXT.actionReindex}
            title={TEXT.actionReindex}
            disabled={reindex.isPending}
            onClick={() => handleReindex(row.original.id)}
          >
            <RefreshCw
              className={cn("h-4 w-4", reindex.isPending && "animate-spin")}
            />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={TEXT.actionDelete}
            title={TEXT.actionDelete}
            onClick={() => setDeleteTarget(row.original)}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ];

  const filtered = kind !== "all" || needle.length > 0;

  return (
    <div>
      <PageHeader
        title={TEXT.title}
        description={TEXT.description}
        actions={
          <Button variant="outline" onClick={() => void documents.refetch()}>
            {TEXT.refresh}
          </Button>
        }
      />

      <div className="mb-6">
        <UploadPanel />
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-56">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="filter-kind"
          >
            {TEXT.filterKind}
          </label>
          <Select
            value={kind}
            onValueChange={(value) => setKind(value as DocumentKind | "all")}
          >
            <SelectTrigger id="filter-kind">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{TEXT.filterAll}</SelectItem>
              {KIND_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="min-w-56 flex-1">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="filter-search"
          >
            {TEXT.filterSearch}
          </label>
          <Input
            id="filter-search"
            value={search}
            placeholder={TEXT.filterSearchPlaceholder}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      {documents.isLoading ? (
        <LoadingState rows={5} />
      ) : documents.isError ? (
        <ErrorState
          error={documents.error}
          onRetry={() => void documents.refetch()}
        />
      ) : rows.length === 0 ? (
        <EmptyState
          title={filtered ? TEXT.emptyFilteredTitle : TEXT.emptyTitle}
          description={
            filtered ? TEXT.emptyFilteredDescription : TEXT.emptyDescription
          }
        />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={rows}
            onRowClick={(document) => setPreviewId(document.id)}
            initialSorting={[{ id: "created_at", desc: true }]}
          />
          <p className="mt-2 text-xs text-muted-foreground">
            {TEXT.countLabel(rows.length)}
          </p>
        </>
      )}

      <PreviewDialog
        documentId={previewId}
        onClose={() => setPreviewId(null)}
        onReindex={handleReindex}
        reindexing={reindex.isPending}
      />

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{TEXT.deleteTitle}</AlertDialogTitle>
            <AlertDialogDescription>
              {TEXT.deleteDescription}
              {deleteTarget ? (
                <span className="mt-2 block font-medium text-foreground">
                  {deleteTarget.filename}
                </span>
              ) : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{TEXT.deleteCancel}</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={handleDelete}
            >
              {TEXT.deleteConfirm}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
