import type { ColumnDef } from "@tanstack/react-table";
import { startOfMonth } from "date-fns";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { StatusBadge, UrgencyBadge } from "@/components/StatusBadges";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CaseDetailSheet } from "@/features/calendar/CaseDetailSheet";
import { DayDialog } from "@/features/calendar/DayDialog";
import { MonthGrid } from "@/features/calendar/MonthGrid";
import { referenceToday } from "@/features/calendar/derive";
import { t } from "@/features/calendar/i18n";
import { formatShortDate, STATUS_LABEL } from "@/lib/format";
import { useCaseYears, useCases } from "@/lib/hooks";
import type { Case, CaseStatus } from "@/lib/types";

const STATUSES: CaseStatus[] = [
  "nowy",
  "zapytania_wyslane",
  "kwerenda",
  "przygotowana_odpowiedz",
  "odpowiedz_wyslana",
];

type ViewMode = "table" | "month";

export default function CalendarPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCaseId = searchParams.get("case");

  const [view, setView] = useState<ViewMode>("table");
  const [year, setYear] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("inflow_asc");
  const [monthOverride, setMonthOverride] = useState<Date | null>(null);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  const years = useCaseYears();
  const { data, isLoading, isError, error, refetch } = useCases({
    year: year === "all" ? undefined : Number(year),
    status: status === "all" ? undefined : (status as CaseStatus),
    q: search || undefined,
    sort,
  });

  const cases = useMemo(() => data ?? [], [data]);
  const referenceDate = useMemo(() => referenceToday(cases), [cases]);
  const month = useMemo(
    () => monthOverride ?? startOfMonth(referenceDate),
    [monthOverride, referenceDate],
  );

  const openCase = (caseId: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("case", caseId);
    setSearchParams(next, { replace: true });
  };

  const closeCase = () => {
    const next = new URLSearchParams(searchParams);
    next.delete("case");
    setSearchParams(next, { replace: true });
  };

  const selectCaseFromDay = (caseId: string) => {
    setSelectedDay(null);
    openCase(caseId);
  };

  const columns = useMemo<ColumnDef<Case, unknown>[]>(
    () => [
      {
        accessorKey: "ordinal",
        header: t.table.ordinal,
        cell: ({ row }) => (
          <span className="tabular-nums text-muted-foreground">
            {row.original.ordinal}
          </span>
        ),
      },
      {
        accessorKey: "case_number",
        header: t.table.caseNumber,
        cell: ({ row }) => (
          <span className="font-mono text-xs">{row.original.case_number}</span>
        ),
      },
      {
        accessorKey: "applicant",
        header: t.table.applicant,
        cell: ({ row }) => (
          <span className="line-clamp-1 max-w-48">{row.original.applicant || "—"}</span>
        ),
      },
      {
        accessorKey: "subject",
        header: t.table.subject,
        cell: ({ row }) => (
          <span className="line-clamp-2 max-w-md">{row.original.subject}</span>
        ),
      },
      {
        accessorKey: "inflow_date",
        header: t.table.inflow,
        cell: ({ row }) => formatShortDate(row.original.inflow_date),
      },
      {
        accessorKey: "deadline",
        header: t.table.deadline,
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="whitespace-nowrap font-medium">
              {formatShortDate(row.original.deadline)}
            </span>
            {row.original.deadline_note ? (
              <span
                className="line-clamp-2 max-w-56 text-xs text-muted-foreground"
                title={row.original.deadline_note}
              >
                {row.original.deadline_note}
              </span>
            ) : null}
          </div>
        ),
      },
      {
        accessorKey: "response_date",
        header: t.table.response,
        cell: ({ row }) =>
          row.original.response_date ? (
            <span className="whitespace-nowrap">
              {formatShortDate(row.original.response_date)}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "days_remaining",
        header: t.table.days,
        cell: ({ row }) => (
          <span className="tabular-nums">{row.original.days_remaining}</span>
        ),
      },
      {
        accessorKey: "urgency",
        header: t.table.urgency,
        cell: ({ row }) => (
          <UrgencyBadge
            urgency={row.original.urgency}
            days={row.original.days_remaining}
          />
        ),
      },
      {
        accessorKey: "status",
        header: t.table.status,
        cell: ({ row }) => <StatusBadge status={row.original.status} />,
      },
      {
        accessorKey: "handler_initials",
        header: t.table.handler,
        cell: ({ row }) => row.original.handler_initials || "—",
      },
    ],
    [],
  );

  return (
    <div>
      <PageHeader
        title={t.page.title}
        description={t.page.description}
        actions={
          <Button variant="outline" onClick={() => void refetch()}>
            {t.page.refresh}
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-40">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="year"
          >
            {t.filters.year}
          </label>
          <Select value={year} onValueChange={setYear}>
            <SelectTrigger id="year">
              <SelectValue placeholder={t.filters.all} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t.filters.all}</SelectItem>
              {(years.data ?? []).map((value) => (
                <SelectItem key={value} value={String(value)}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="w-56">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="status"
          >
            {t.filters.status}
          </label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger id="status">
              <SelectValue placeholder={t.filters.all} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t.filters.all}</SelectItem>
              {STATUSES.map((value) => (
                <SelectItem key={value} value={value}>
                  {STATUS_LABEL[value]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="w-56">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="sort"
          >
            {t.filters.sort}
          </label>
          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger id="sort">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="deadline_asc">
                {t.filters.sortDeadlineAsc}
              </SelectItem>
              <SelectItem value="deadline_desc">
                {t.filters.sortDeadlineDesc}
              </SelectItem>
              <SelectItem value="inflow_asc">
                {t.filters.sortInflowAsc}
              </SelectItem>
              <SelectItem value="inflow_desc">
                {t.filters.sortInflowDesc}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="min-w-56 flex-1">
          <label
            className="mb-1 block text-xs text-muted-foreground"
            htmlFor="search"
          >
            {t.filters.search}
          </label>
          <Input
            id="search"
            placeholder={t.filters.searchPlaceholder}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div>
          <span className="mb-1 block text-xs text-muted-foreground">
            {t.views.label}
          </span>
          <Tabs
            value={view}
            onValueChange={(value) => setView(value as ViewMode)}
          >
            <TabsList>
              <TabsTrigger value="table">{t.views.table}</TabsTrigger>
              <TabsTrigger value="month">{t.views.month}</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {isLoading ? (
        <LoadingState rows={6} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : cases.length === 0 ? (
        <EmptyState
          title="Brak wniosków dla wybranych filtrów"
          description="Zmień rok, stan sprawy lub wyczyść pole wyszukiwania."
        />
      ) : (
        <>
          {view === "table" ? (
            <DataTable
              columns={columns}
              data={cases}
              onRowClick={(row) => openCase(row.id)}
              emptyMessage={t.table.empty}
              initialSorting={[{ id: "deadline", desc: false }]}
            />
          ) : (
            <MonthGrid
              cases={cases}
              month={month}
              referenceDate={referenceDate}
              onMonthChange={setMonthOverride}
              onSelectDay={setSelectedDay}
            />
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            {t.page.footer(cases.length)}
          </p>
        </>
      )}

      <DayDialog
        day={selectedDay}
        cases={cases}
        onClose={() => setSelectedDay(null)}
        onSelectCase={selectCaseFromDay}
      />

      <CaseDetailSheet caseId={selectedCaseId} onClose={closeCase} />
    </div>
  );
}
