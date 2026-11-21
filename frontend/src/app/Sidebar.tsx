import { Search } from "lucide-react";
import { NavLink } from "react-router-dom";

import { visibleFeatures } from "@/app/registry";
import { modifierKeyLabel } from "@/app/shortcuts";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Sidebar({ onOpenPalette }: { onOpenPalette: () => void }) {
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-muted/30 md:flex md:flex-col">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
          AU
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold">Asystent urzędnika</p>
          <p className="text-xs text-muted-foreground">Miasto Bydgoszcz</p>
        </div>
      </div>

      <div className="p-2">
        <Button
          type="button"
          variant="outline"
          onClick={onOpenPalette}
          className="w-full justify-start gap-2 text-muted-foreground"
          aria-label="Otwórz paletę poleceń"
        >
          <Search className="h-4 w-4" aria-hidden="true" />
          <span className="flex-1 text-left">Szukaj…</span>
          <kbd className="rounded border bg-muted px-1.5 font-mono text-[10px]">
            {modifierKeyLabel()} K
          </kbd>
        </Button>
      </div>

      <nav
        aria-label="Menu główne"
        className="flex-1 space-y-1 overflow-y-auto p-2 pt-0"
      >
        {visibleFeatures.map((feature) => {
          const Icon = feature.icon;
          return (
            <NavLink
              key={feature.id}
              to={`/${feature.path}`}
              end={feature.path === ""}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
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

      <div className="border-t p-3 text-xs text-muted-foreground">
        Wersja demo · dane fikcyjne
      </div>
    </aside>
  );
}
