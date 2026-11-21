import { useQuery } from "@tanstack/react-query";
import { CircleDot, Keyboard, Menu, Search } from "lucide-react";
import { useState } from "react";
import { NavLink } from "react-router-dom";

import { Breadcrumbs } from "@/app/Breadcrumbs";
import { visibleFeatures } from "@/app/registry";
import { modifierKeyLabel } from "@/app/shortcuts";
import { ThemeToggle } from "@/app/ThemeToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { RemindersBell } from "@/features/reminders/RemindersBell";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Health = {
  status: "ok" | "degraded";
  version: string;
  modules: Record<string, "fake" | "real" | "error">;
};

type TopbarProps = {
  onOpenPalette: () => void;
  onOpenHelp: () => void;
};

export function Topbar({ onOpenPalette, onOpenHelp }: TopbarProps) {
  const [open, setOpen] = useState(false);
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
    refetchInterval: 60_000,
  });

  const realCount = data
    ? Object.values(data.modules).filter((mode) => mode === "real").length
    : 0;

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b bg-background/95 px-3 backdrop-blur md:px-4">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Otwórz menu"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <SheetHeader className="border-b p-4">
            <SheetTitle>Asystent urzędnika</SheetTitle>
            <SheetDescription className="text-xs">
              Miasto Bydgoszcz
            </SheetDescription>
          </SheetHeader>
          <nav aria-label="Menu główne" className="space-y-1 p-2">
            {visibleFeatures.map((feature) => {
              const Icon = feature.icon;
              return (
                <NavLink
                  key={feature.id}
                  to={`/${feature.path}`}
                  end={feature.path === ""}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span className="truncate">{feature.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </SheetContent>
      </Sheet>

      <Breadcrumbs className="hidden sm:block" />

      <div className="flex-1" />

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onOpenPalette}
        className="gap-2"
        aria-label="Otwórz paletę poleceń"
      >
        <Search className="h-4 w-4" aria-hidden="true" />
        <span className="hidden sm:inline">Szukaj</span>
        <kbd className="hidden rounded border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground md:inline">
          {modifierKeyLabel()} K
        </kbd>
      </Button>

      <RemindersBell />

      <ThemeToggle />

      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={onOpenHelp}
        aria-label="Skróty klawiszowe"
        title="Skróty klawiszowe"
      >
        <Keyboard className="h-4 w-4" aria-hidden="true" />
      </Button>

      <Badge variant="outline" className="hidden gap-1.5 lg:inline-flex">
        <CircleDot
          className={cn(
            "h-3 w-3",
            isError
              ? "text-red-500"
              : data?.status === "ok"
                ? "text-emerald-500"
                : "text-amber-500",
          )}
          aria-hidden="true"
        />
        {isError
          ? "Backend niedostępny"
          : data
            ? `API ${data.version} · ${realCount}/${Object.keys(data.modules).length} modułów realnych`
            : "Łączenie…"}
      </Badge>
    </header>
  );
}
