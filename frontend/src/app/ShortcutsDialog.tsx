import type { ReactNode } from "react";

import { visibleFeatures } from "@/app/registry";
import { modifierKeyLabel, navShortcuts } from "@/app/shortcuts";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="inline-flex h-6 min-w-6 items-center justify-center rounded border bg-muted px-1.5 font-mono text-xs text-foreground">
      {children}
    </kbd>
  );
}

function ShortcutRow({
  keys,
  label,
}: {
  keys: ReactNode;
  label: string;
}) {
  return (
    <li className="flex items-center justify-between gap-4 py-1.5">
      <span className="text-sm">{label}</span>
      <span className="flex shrink-0 items-center gap-1">{keys}</span>
    </li>
  );
}

const GLOBAL_SHORTCUTS: { keys: string[]; label: string }[] = [
  { keys: ["?"], label: "Pokaż tę listę skrótów" },
  { keys: ["Esc"], label: "Zamknij okno albo panel" },
  { keys: ["Tab"], label: "Przejdź do następnego elementu" },
  { keys: ["Enter"], label: "Otwórz zaznaczony wiersz albo pozycję" },
];

export function ShortcutsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigation = navShortcuts(visibleFeatures);
  const modifier = modifierKeyLabel();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Skróty klawiszowe</DialogTitle>
          <DialogDescription>
            Skróty działają na każdym ekranie. W polach tekstowych nawigacja
            literami jest wyłączona, żeby nie przeszkadzać w pisaniu.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <section aria-labelledby="shortcuts-navigation">
            <h3
              id="shortcuts-navigation"
              className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Przejdź do ekranu
            </h3>
            <ul className="divide-y">
              {navigation.map((shortcut) => (
                <ShortcutRow
                  key={shortcut.featureId}
                  label={shortcut.label}
                  keys={
                    <>
                      <Kbd>g</Kbd>
                      <span className="text-xs text-muted-foreground">potem</span>
                      <Kbd>{shortcut.key}</Kbd>
                    </>
                  }
                />
              ))}
            </ul>
          </section>

          <section aria-labelledby="shortcuts-global">
            <h3
              id="shortcuts-global"
              className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Ogólne
            </h3>
            <ul className="divide-y">
              <ShortcutRow
                label="Otwórz paletę poleceń"
                keys={
                  <>
                    <Kbd>{modifier}</Kbd>
                    <Kbd>K</Kbd>
                  </>
                }
              />
              {GLOBAL_SHORTCUTS.map((shortcut) => (
                <ShortcutRow
                  key={shortcut.label}
                  label={shortcut.label}
                  keys={shortcut.keys.map((key) => (
                    <Kbd key={key}>{key}</Kbd>
                  ))}
                />
              ))}
            </ul>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
