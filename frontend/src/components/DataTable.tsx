import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { type KeyboardEvent, useState } from "react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

type DataTableProps<TData> = {
  columns: ColumnDef<TData, unknown>[];
  data: TData[];
  onRowClick?: (row: TData) => void;
  emptyMessage?: string;
  initialSorting?: SortingState;
  /** Opis tabeli dla czytników ekranu. */
  label?: string;
  /** Minimalna szerokość — poniżej niej tabela przewija się poziomo. */
  minWidthClass?: string;
};

function headerText<TData>(column: ColumnDef<TData, unknown>): string {
  const header = column.header;
  if (typeof header === "string") return header;
  return column.id ?? "";
}

export function DataTable<TData>({
  columns,
  data,
  onRowClick,
  emptyMessage = "Brak danych do wyświetlenia.",
  initialSorting = [],
  label = "Tabela danych",
  minWidthClass = "min-w-[640px]",
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const activate = (row: TData) => {
    onRowClick?.(row);
  };

  const handleRowKeyDown = (
    event: KeyboardEvent<HTMLTableRowElement>,
    row: TData,
  ) => {
    if (!onRowClick) return;
    // Enter na przycisku w komórce należy do przycisku, nie do wiersza.
    if (event.target !== event.currentTarget) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    activate(row);
  };

  return (
    <div className="rounded-lg border">
      <Table aria-label={label} className={minWidthClass}>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const canSort = header.column.getCanSort();
                const sorted = header.column.getIsSorted();
                const text = headerText(header.column.columnDef);
                return (
                  <TableHead
                    key={header.id}
                    aria-sort={
                      sorted === "asc"
                        ? "ascending"
                        : sorted === "desc"
                          ? "descending"
                          : canSort
                            ? "none"
                            : undefined
                    }
                  >
                    {header.isPlaceholder ? null : (
                      <button
                        type="button"
                        disabled={!canSort}
                        onClick={header.column.getToggleSortingHandler()}
                        aria-label={
                          canSort
                            ? `Sortuj według kolumny ${text}`
                            : undefined
                        }
                        className={cn(
                          "inline-flex items-center gap-1 rounded-sm",
                          canSort && "hover:text-foreground",
                        )}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                        {canSort ? (
                          sorted === "asc" ? (
                            <ArrowUp className="h-3 w-3" aria-hidden="true" />
                          ) : sorted === "desc" ? (
                            <ArrowDown className="h-3 w-3" aria-hidden="true" />
                          ) : (
                            <ChevronsUpDown
                              className="h-3 w-3 opacity-40"
                              aria-hidden="true"
                            />
                          )
                        ) : null}
                      </button>
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="py-10 text-center text-sm text-muted-foreground"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                onClick={() => activate(row.original)}
                onKeyDown={(event) => handleRowKeyDown(event, row.original)}
                tabIndex={onRowClick ? 0 : undefined}
                className={cn(
                  onRowClick &&
                    "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
