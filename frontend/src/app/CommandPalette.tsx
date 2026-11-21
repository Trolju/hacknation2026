import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  FilePlus2,
  FileText,
  FileUp,
  Keyboard,
  type LucideIcon,
  Moon,
  RefreshCw,
  Search,
  Sun,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  filterEntries,
  shouldSearchCases,
  type PaletteEntry,
} from "@/app/commandItems";
import { visibleFeatures } from "@/app/registry";
import { modifierKeyLabel } from "@/app/shortcuts";
import { useTheme } from "@/app/theme";
import { useDebouncedValue } from "@/app/useDebouncedValue";
import { apiErrorMessage } from "@/components/errorMessages";
import { NewCaseDialog } from "@/components/NewCaseDialog";
import { UrgencyBadge } from "@/components/StatusBadges";
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { formatShortDate } from "@/lib/format";
import { useCases } from "@/lib/hooks";
import type { Case } from "@/lib/types";

type PaletteCommand = PaletteEntry & {
  icon: LucideIcon;
  run: () => void;
};

type PaletteMode = "all" | "cases";

function PaletteItem({ command }: { command: PaletteCommand }) {
  const Icon = command.icon;
  return (
    <CommandItem
      value={command.id}
      keywords={command.keywords}
      onSelect={command.run}
    >
      <Icon
        className="h-4 w-4 shrink-0 text-muted-foreground"
        aria-hidden="true"
      />
      <span className="flex min-w-0 flex-col">
        <span className="truncate">{command.label}</span>
        {command.description ? (
          <span className="truncate text-xs text-muted-foreground">
            {command.description}
          </span>
        ) : null}
      </span>
    </CommandItem>
  );
}

function CaseResultsQuery({
  term,
  onSelect,
}: {
  term: string;
  onSelect: (item: Case) => void;
}) {
  const { data, isLoading, isError, error } = useCases({
    q: term,
    sort: "deadline_asc",
  });

  const cases = useMemo(() => (data ?? []).slice(0, 8), [data]);

  if (isLoading) {
    return (
      <div className="space-y-2 p-2" aria-busy="true">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="px-3 py-4 text-sm text-destructive">
        {apiErrorMessage(error)}
      </p>
    );
  }

  if (cases.length === 0) {
    return (
      <p className="px-3 py-4 text-sm text-muted-foreground">
        Brak spraw pasujących do „{term}”.
      </p>
    );
  }

  return (
    <>
      {cases.map((item) => (
        <CommandItem
          key={item.id}
          value={`case-${item.id}`}
          onSelect={() => onSelect(item)}
          className="items-start"
        >
          <FileText
            className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
            aria-hidden="true"
          />
          <span className="flex min-w-0 flex-col gap-0.5">
            <span className="truncate font-medium">{item.subject}</span>
            <span className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
              <span className="font-mono">{item.case_number}</span>
              <span>termin {formatShortDate(item.deadline)}</span>
            </span>
          </span>
          <span className="ml-auto shrink-0">
            <UrgencyBadge
              urgency={item.urgency}
              days={item.days_remaining}
            />
          </span>
        </CommandItem>
      ))}
    </>
  );
}

function CaseResults({
  term,
  onSelect,
}: {
  term: string;
  onSelect: (item: Case) => void;
}) {
  if (!shouldSearchCases(term)) {
    return (
      <p className="px-3 py-4 text-sm text-muted-foreground">
        Wpisz co najmniej dwa znaki numeru sprawy albo tematu.
      </p>
    );
  }
  return <CaseResultsQuery term={term} onSelect={onSelect} />;
}

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onShowShortcuts: () => void;
};

/**
 * Paleta poleceń pod `Cmd/Ctrl+K`.
 *
 * Trzy grupy: ekrany z rejestru, szybkie akcje i sprawy z `GET /api/cases?q=`.
 * Filtrowanie ekranów i akcji dzieje się lokalnie (`shouldFilter={false}`),
 * a sprawy dopasowuje backend — dzięki temu szukanie działa też po numerze
 * sprawy, którego nie ma w tekście pozycji menu.
 */
export function CommandPalette({
  open,
  onOpenChange,
  onShowShortcuts,
}: CommandPaletteProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { theme, toggle } = useTheme();

  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<PaletteMode>("all");
  const [newCaseOpen, setNewCaseOpen] = useState(false);

  const debouncedQuery = useDebouncedValue(query, 250);

  const handleOpenChange = useCallback(
    (next: boolean) => {
      onOpenChange(next);
      if (!next) {
        setQuery("");
        setMode("all");
      }
    },
    [onOpenChange],
  );

  const go = useCallback(
    (path: string) => {
      handleOpenChange(false);
      navigate(path);
    },
    [handleOpenChange, navigate],
  );

  const navigation = useMemo<PaletteCommand[]>(
    () =>
      visibleFeatures.map((feature) => ({
        id: `nav-${feature.id}`,
        label: feature.label,
        description: feature.description,
        keywords: [feature.path, feature.id],
        icon: feature.icon,
        run: () => go(`/${feature.path}`),
      })),
    [go],
  );

  const actions = useMemo<PaletteCommand[]>(
    () => [
      {
        id: "action-new-case",
        label: "Nowy wniosek",
        description: "Dodaj sprawę do kalendarza terminów",
        keywords: ["dodaj", "utwórz", "sprawa", "wniosek"],
        icon: FilePlus2,
        run: () => {
          handleOpenChange(false);
          setNewCaseOpen(true);
        },
      },
      {
        id: "action-upload",
        label: "Wgraj dokument",
        description: "Przejdź do ekranu dokumentów i wgraj plik",
        keywords: ["plik", "pdf", "docx", "dokument", "wniosek"],
        icon: FileUp,
        run: () => go("/dokumenty"),
      },
      {
        id: "action-find-case",
        label: "Przejdź do sprawy…",
        description: "Szukaj sprawy po numerze albo temacie",
        keywords: ["szukaj", "sprawa", "numer", "temat"],
        icon: Search,
        run: () => {
          setMode("cases");
          setQuery("");
        },
      },
      {
        id: "action-theme",
        label: theme === "dark" ? "Włącz motyw jasny" : "Włącz motyw ciemny",
        description: "Przełącz wygląd interfejsu",
        keywords: ["motyw", "ciemny", "jasny", "wyglad", "theme"],
        icon: theme === "dark" ? Sun : Moon,
        run: () => toggle(),
      },
      {
        id: "action-shortcuts",
        label: "Pokaż skróty klawiszowe",
        description: "Lista wszystkich skrótów",
        keywords: ["klawiatura", "pomoc", "skroty"],
        icon: Keyboard,
        run: () => {
          handleOpenChange(false);
          onShowShortcuts();
        },
      },
      {
        id: "action-refresh",
        label: "Odśwież dane",
        description: "Ponownie pobierz dane z serwera",
        keywords: ["odswiez", "refresh", "przeladuj", "aktualizuj"],
        icon: RefreshCw,
        run: () => {
          void queryClient.invalidateQueries();
          handleOpenChange(false);
        },
      },
    ],
    [go, handleOpenChange, onShowShortcuts, queryClient, theme, toggle],
  );

  const visibleNavigation = useMemo(
    () => filterEntries(navigation, query),
    [navigation, query],
  );
  const visibleActions = useMemo(
    () => filterEntries(actions, query),
    [actions, query],
  );

  const showCases = mode === "cases" || shouldSearchCases(query);
  const nothingFound =
    mode === "all" &&
    visibleNavigation.length === 0 &&
    visibleActions.length === 0 &&
    !showCases;

  return (
    <>
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className="overflow-hidden p-0 sm:max-w-xl">
          <DialogTitle className="sr-only">Paleta poleceń</DialogTitle>
          <DialogDescription className="sr-only">
            Szukaj ekranów, szybkich akcji i spraw. Wpisz numer sprawy albo
            fragment tematu.
          </DialogDescription>
          <Command
            shouldFilter={false}
            className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-2.5"
          >
            <CommandInput
              value={query}
              onValueChange={setQuery}
              aria-label="Szukaj w palecie poleceń"
              placeholder={
                mode === "cases"
                  ? "Numer sprawy albo fragment tematu…"
                  : "Szukaj ekranu, akcji albo sprawy…"
              }
              className="h-12 pr-10"
            />
            <CommandList className="max-h-[min(60vh,420px)]">
              {mode === "all" && visibleNavigation.length > 0 ? (
                <CommandGroup heading="Ekrany">
                  {visibleNavigation.map((command) => (
                    <PaletteItem key={command.id} command={command} />
                  ))}
                </CommandGroup>
              ) : null}

              {mode === "all" && visibleActions.length > 0 ? (
                <CommandGroup heading="Szybkie akcje">
                  {visibleActions.map((command) => (
                    <PaletteItem key={command.id} command={command} />
                  ))}
                </CommandGroup>
              ) : null}

              {showCases ? (
                <CommandGroup heading="Sprawy">
                  {mode === "cases" ? (
                    <CommandItem
                      value="action-back-to-all"
                      onSelect={() => {
                        setMode("all");
                        setQuery("");
                      }}
                    >
                      <ArrowLeft
                        className="h-4 w-4 shrink-0 text-muted-foreground"
                        aria-hidden="true"
                      />
                      <span>Wróć do wszystkich poleceń</span>
                    </CommandItem>
                  ) : null}
                  <CaseResults
                    term={debouncedQuery}
                    onSelect={(item) => go(`/kalendarz?case=${item.id}`)}
                  />
                </CommandGroup>
              ) : null}

              {nothingFound ? (
                <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                  Nic nie pasuje do „{query}”. Spróbuj innej frazy.
                </p>
              ) : null}
            </CommandList>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t px-3 py-2 text-xs text-muted-foreground">
              <span>Strzałki wybierają, Enter otwiera, Esc zamyka</span>
              <span className="font-mono">
                {mode === "cases"
                  ? "tryb: sprawy"
                  : `${modifierKeyLabel()} + K`}
              </span>
            </div>
          </Command>
        </DialogContent>
      </Dialog>

      <NewCaseDialog open={newCaseOpen} onOpenChange={setNewCaseOpen} />
    </>
  );
}
