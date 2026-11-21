import { Compass } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <Compass
        className="h-10 w-10 text-muted-foreground"
        aria-hidden="true"
      />
      <p className="text-5xl font-semibold text-muted-foreground">404</p>
      <h1 className="text-xl font-semibold">Nie ma takiego ekranu</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Adres nie odpowiada żadnemu modułowi aplikacji. Wróć do pulpitu albo
        otwórz paletę poleceń skrótem Ctrl+K i wybierz ekran z listy.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        <Button asChild>
          <Link to="/">Przejdź do pulpitu</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/kalendarz">Kalendarz terminów</Link>
        </Button>
      </div>
    </div>
  );
}
