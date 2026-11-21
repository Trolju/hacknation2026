import { useRef } from "react";

import { ErrorState, LoadingState } from "@/components/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useArchiveCase } from "@/features/archive/api";
import { TEXT } from "@/features/archive/i18n";

type ArchiveCaseSheetProps = {
  archiveId: string | null;
  onClose: () => void;
  onUseInResponse: (archiveId: string, caseNumber: string) => void;
};

export function ArchiveCaseSheet({
  archiveId,
  onClose,
  onUseInResponse,
}: ArchiveCaseSheetProps) {
  // Podczas animacji zamykania `archiveId` jest już puste — trzymamy ostatnie
  // otwarte id, żeby panel nie mrugnął pustką.
  const lastId = useRef<string | null>(null);
  if (archiveId) lastId.current = archiveId;
  const shownId = archiveId ?? lastId.current;

  const detail = useArchiveCase(shownId);
  const data = detail.data;

  return (
    <Sheet
      open={Boolean(archiveId)}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle className="font-mono text-base">
            {data?.case_number ?? TEXT.detail.title}
          </SheetTitle>
          <SheetDescription>{data?.subject ?? TEXT.detail.loading}</SheetDescription>
        </SheetHeader>

        {detail.isLoading ? (
          <div className="mt-4">
            <LoadingState rows={4} />
          </div>
        ) : detail.isError ? (
          <div className="mt-4">
            <ErrorState error={detail.error} onRetry={() => void detail.refetch()} />
          </div>
        ) : data ? (
          <div className="mt-4 space-y-6">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{TEXT.yearLabel(data.year)}</Badge>
              <Badge variant="secondary" className="font-mono">
                {data.archive_id}
              </Badge>
            </div>

            <section>
              <h3 className="mb-2 text-sm font-semibold">{TEXT.detail.request}</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed">
                {data.request_text}
              </p>
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 text-sm font-semibold">{TEXT.detail.response}</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed">
                {data.response_text}
              </p>
            </section>

            <Separator />

            <section>
              <h3 className="mb-2 text-sm font-semibold">{TEXT.detail.departments}</h3>
              {data.departments.length > 0 ? (
                <ul className="flex flex-wrap gap-2">
                  {data.departments.map((department) => (
                    <li key={department}>
                      <Badge variant="outline">{department}</Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {TEXT.detail.noDepartments}
                </p>
              )}
            </section>

            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => onUseInResponse(data.archive_id, data.case_number)}
              >
                {TEXT.useInResponse}
              </Button>
              <Button variant="outline" onClick={onClose}>
                {TEXT.detail.close}
              </Button>
            </div>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
