import { useCallback, useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { normalizePath } from "@/app/breadcrumbs";
import { CommandPalette } from "@/app/CommandPalette";
import { visibleFeatures } from "@/app/registry";
import { ShortcutsDialog } from "@/app/ShortcutsDialog";
import { Sidebar } from "@/app/Sidebar";
import { Topbar } from "@/app/Topbar";
import { navShortcuts } from "@/app/shortcuts";
import { useDocumentTitle } from "@/app/useDocumentTitle";
import { useGlobalShortcuts } from "@/app/useGlobalShortcuts";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export function Layout() {
  const location = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const shortcuts = useMemo(() => navShortcuts(visibleFeatures), []);

  const pageLabel = useMemo(() => {
    const path = normalizePath(location.pathname);
    const feature = visibleFeatures.find(
      (item) => normalizePath(`/${item.path}`) === path,
    );
    return feature?.label ?? "Nie znaleziono ekranu";
  }, [location.pathname]);

  useDocumentTitle(pageLabel);

  const openPalette = useCallback(() => setPaletteOpen((open) => !open), []);
  const openHelp = useCallback(() => setHelpOpen(true), []);

  useGlobalShortcuts({
    shortcuts,
    onOpenPalette: openPalette,
    onOpenHelp: openHelp,
  });

  return (
    <div className="flex min-h-screen bg-background">
      <a href="#tresc" className="skip-link">
        Przejdź do treści
      </a>

      <Sidebar onOpenPalette={openPalette} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenPalette={openPalette} onOpenHelp={openHelp} />
        <main
          id="tresc"
          tabIndex={-1}
          className="flex-1 overflow-x-hidden p-4 md:p-6"
        >
          <ErrorBoundary key={location.pathname} scope={pageLabel}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        onShowShortcuts={openHelp}
      />
      <ShortcutsDialog open={helpOpen} onOpenChange={setHelpOpen} />
    </div>
  );
}
