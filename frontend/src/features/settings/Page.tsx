import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  FlaskConical,
  Loader2,
  RefreshCw,
  WifiOff,
  XCircle,
} from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { ErrorState, InlineSpinner, LoadingState } from "@/components/States";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  type InferenceProvider,
  type InferenceStatus,
  type ModelInfo,
  useAppMeta,
  useInferenceHealth,
  useInferenceModels,
  useTestInference,
} from "@/features/settings/api";
import { MODE_LABEL, describeModule } from "@/features/settings/modules";

const MODEL_STORAGE_KEY = "asystent.llm.model";

const PROVIDER_LABEL: Record<InferenceProvider, string> = {
  fake: "Atrapa (bez modelu)",
  llamacpp: "llama.cpp",
  ollama: "Ollama",
  openai: "OpenAI",
  mistral: "Mistral (La Plateforme)",
};

const STATUS_LABEL: Record<InferenceStatus, string> = {
  ok: "Działa",
  degraded: "Ograniczony",
  down: "Niedostępny",
};

const STATUS_VARIANT: Record<InferenceStatus, "default" | "secondary" | "destructive"> = {
  ok: "default",
  degraded: "secondary",
  down: "destructive",
};

function readStoredModel(): string {
  try {
    return window.localStorage.getItem(MODEL_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function storeModel(modelId: string): void {
  try {
    window.localStorage.setItem(MODEL_STORAGE_KEY, modelId);
  } catch {
    /* tryb prywatny przeglądarki — wybór zostaje tylko w pamięci sesji */
  }
}

function formatLatency(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(2)} s`;
  return `${Math.round(value)} ms`;
}

function modelOptionText(model: ModelInfo): string {
  const suffix = model.local ? "" : " (chmura)";
  return `${model.label}${suffix}`;
}

function StatusIcon({ status }: { status: InferenceStatus }) {
  if (status === "ok")
    return (
      <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
    );
  if (status === "degraded")
    return (
      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
    );
  return <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <div className="text-right">{value}</div>
    </div>
  );
}

export default function SettingsPage() {
  const meta = useAppMeta();
  const health = useInferenceHealth();
  const models = useInferenceModels();
  const test = useTestInference();

  const [selectedModel, setSelectedModel] = useState<string>(() => readStoredModel());

  useEffect(() => {
    if (!models.data?.length) return;
    if (models.data.some((model) => model.id === selectedModel)) return;
    const fallback =
      health.data?.model ??
      models.data.find((model) => model.recommended)?.id ??
      models.data[0]?.id;
    if (fallback) setSelectedModel(fallback);
  }, [selectedModel, health.data, models.data]);

  useEffect(() => {
    if (selectedModel) storeModel(selectedModel);
  }, [selectedModel]);

  if (meta.isLoading) return <LoadingState rows={3} variant="list" />;
  if (meta.isError) {
    return <ErrorState error={meta.error} onRetry={() => void meta.refetch()} />;
  }

  const offline = meta.data?.offline ?? false;
  const modes = meta.data?.module_modes ?? {};
  const moduleCount = Object.keys(modes).length;
  const fakeModules = Object.values(modes).filter((mode) => mode === "fake").length;
  const activeModel = health.data?.model ?? "";
  const status = health.data?.status ?? "down";
  const selectionDiffers = Boolean(
    selectedModel && activeModel && selectedModel !== activeModel,
  );

  return (
    <div>
      <PageHeader
        title="Ustawienia"
        description="Stan środowiska, warstwa modeli językowych i tryb pracy modułów."
        actions={
          <Button
            variant="outline"
            onClick={() => {
              void meta.refetch();
              void health.refetch();
              void models.refetch();
            }}
          >
            <RefreshCw className="h-4 w-4" />
            Odśwież
          </Button>
        }
      />

      {offline ? (
        <Alert variant="warning" className="mb-4">
          <WifiOff className="h-4 w-4" />
          <AlertTitle>Tryb offline</AlertTitle>
          <AlertDescription>
            Aplikacja nie łączy się z internetem ani z serwerem modelu. Odpowiedzi
            przygotowuje atrapa, a test połączenia jest zablokowany. Aby korzystać
            z modelu, ustaw <code>OFFLINE=false</code> i uruchom lokalny serwer modelu.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Środowisko</CardTitle>
            <CardDescription>{meta.data?.name}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row
              label="Wersja"
              value={<span className="font-mono">{meta.data?.version}</span>}
            />
            <Row
              label="Tryb offline"
              value={
                <Badge variant={offline ? "default" : "secondary"}>
                  {offline ? "włączony" : "wyłączony"}
                </Badge>
              }
            />
            <Row
              label="Moduły na atrapie"
              value={
                <span className="tabular-nums">
                  {fakeModules} z {moduleCount}
                </span>
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Warstwa modeli</CardTitle>
            <CardDescription>
              {health.data
                ? `${PROVIDER_LABEL[health.data.provider]} · ${health.data.model}`
                : "Brak danych o modelu"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {health.isLoading ? (
              <InlineSpinner label="Sprawdzanie stanu modelu…" />
            ) : health.isError ? (
              <ErrorState error={health.error} onRetry={() => void health.refetch()} />
            ) : (
              <>
                <Row
                  label="Stan"
                  value={
                    <span className="inline-flex items-center gap-1.5">
                      <StatusIcon status={status} />
                      <Badge variant={STATUS_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>
                    </span>
                  }
                />
                <Row
                  label="Opóźnienie"
                  value={
                    <span className="tabular-nums">
                      {health.data?.latency_ms != null
                        ? formatLatency(health.data.latency_ms)
                        : "—"}
                    </span>
                  }
                />
                <Row
                  label="Dostawca"
                  value={
                    <Badge variant="outline">
                      {health.data ? PROVIDER_LABEL[health.data.provider] : "—"}
                    </Badge>
                  }
                />
                {health.data?.message ? (
                  <p className="text-xs text-muted-foreground">{health.data.message}</p>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Model językowy</CardTitle>
          <CardDescription>
            Wybierz model z katalogu i sprawdź, czy serwer modelu odpowiada.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
            <div className="space-y-1.5">
              <label htmlFor="model" className="text-sm font-medium">
                Model
              </label>
              {models.isLoading ? (
                <InlineSpinner label="Pobieranie katalogu modeli…" />
              ) : models.isError ? (
                <ErrorState error={models.error} onRetry={() => void models.refetch()} />
              ) : (
                <Select
                  value={selectedModel}
                  onValueChange={(value) => {
                    setSelectedModel(value);
                    test.reset();
                  }}
                  disabled={!models.data?.length}
                >
                  <SelectTrigger id="model">
                    <SelectValue placeholder="Wybierz model" />
                  </SelectTrigger>
                  <SelectContent>
                    {(models.data ?? []).map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {modelOptionText(model)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <Button
              onClick={() => test.mutate()}
              disabled={test.isPending || offline}
              title={offline ? "Test połączenia jest zablokowany w trybie offline" : undefined}
            >
              {test.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FlaskConical className="h-4 w-4" />
              )}
              Testuj połączenie
            </Button>
          </div>

          <div className="space-y-2 text-sm">
            <Row
              label="Model aktywny"
              value={<span className="font-mono text-xs">{activeModel || "—"}</span>}
            />
            <Row
              label="Wybrany model"
              value={<span className="font-mono text-xs">{selectedModel || "—"}</span>}
            />
          </div>

          {offline ? (
            <p className="text-xs text-muted-foreground">
              Test połączenia jest niedostępny w trybie offline — aplikacja nie wykonuje
              żadnych połączeń sieciowych.
            </p>
          ) : null}

          {selectionDiffers ? (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Wybrany model nie jest aktywny</AlertTitle>
              <AlertDescription>
                Aplikacja korzysta z modelu <code>{activeModel}</code>. Aby go zmienić,
                ustaw <code>LLM_MODEL={selectedModel}</code> i uruchom usługę ponownie.
                Test połączenia sprawdza model aktywny.
              </AlertDescription>
            </Alert>
          ) : null}

          {test.isError ? (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Nie udało się wykonać testu</AlertTitle>
              <AlertDescription>
                {test.error instanceof Error
                  ? test.error.message
                  : "Nieznany błąd połączenia z modelem."}
              </AlertDescription>
            </Alert>
          ) : null}

          {test.data ? (
            test.data.ok ? (
              <Alert>
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <AlertTitle>Połączenie działa</AlertTitle>
                <AlertDescription className="space-y-2">
                  <p>
                    Opóźnienie odpowiedzi:{" "}
                    <span className="font-medium tabular-nums">
                      {formatLatency(test.data.latency_ms)}
                    </span>
                  </p>
                  {test.data.output ? (
                    <blockquote className="rounded border-l-2 border-emerald-300 bg-muted/50 px-3 py-2 text-xs">
                      {test.data.output}
                    </blockquote>
                  ) : null}
                </AlertDescription>
              </Alert>
            ) : (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertTitle>Test nieudany</AlertTitle>
                <AlertDescription className="space-y-2">
                  <p>{test.data.error ?? "Model nie odpowiedział."}</p>
                  <p className="text-xs">
                    Czas oczekiwania:{" "}
                    <span className="tabular-nums">
                      {formatLatency(test.data.latency_ms)}
                    </span>
                  </p>
                </AlertDescription>
              </Alert>
            )
          ) : null}
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Katalog modeli</CardTitle>
          <CardDescription>
            Modele z konfiguracji aplikacji oraz te zgłoszone przez serwer modelu.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {models.isLoading ? (
            <InlineSpinner label="Pobieranie katalogu modeli…" />
          ) : models.isError ? (
            <ErrorState error={models.error} onRetry={() => void models.refetch()} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Dostawca</TableHead>
                  <TableHead>Środowisko</TableHead>
                  <TableHead>Rozmiar</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(models.data ?? []).map((model) => (
                  <TableRow key={model.id}>
                    <TableCell>
                      <span className="font-medium">{model.label}</span>
                      {model.id === activeModel ? (
                        <Badge className="ml-2" variant="default">
                          aktywny
                        </Badge>
                      ) : null}
                      {model.recommended ? (
                        <Badge className="ml-2" variant="secondary">
                          zalecany
                        </Badge>
                      ) : null}
                      <span className="block font-mono text-xs text-muted-foreground">
                        {model.id}
                      </span>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{model.provider}</TableCell>
                    <TableCell>{model.local ? "lokalne" : "chmura"}</TableCell>
                    <TableCell className="tabular-nums">
                      {model.size_gb != null ? `${model.size_gb} GB` : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Tryb modułów</CardTitle>
          <CardDescription>
            {fakeModules === 0
              ? "Wszystkie moduły działają na danych rzeczywistych."
              : `${fakeModules} z ${moduleCount} modułów działa na atrapie — dane są demonstracyjne, a wyniki zawsze takie same.`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert
            variant={fakeModules === 0 ? "default" : "warning"}
            className="dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100 dark:[&>svg]:text-amber-400"
          >
            <Cpu className="h-4 w-4" />
            <AlertTitle>Co to znaczy w praktyce</AlertTitle>
            <AlertDescription>
              Atrapa nie wysyła niczego na zewnątrz i nie potrzebuje modelu: pokazuje
              ustalone dane demonstracyjne. Moduł realny przetwarza prawdziwe dane —
              wgrane pliki, bazę urzędu albo model językowy. Tryb zmienia się zmienną{" "}
              <code>MODULE_MODE_&lt;NAZWA&gt;</code>, bez zmian w kodzie.
            </AlertDescription>
          </Alert>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Moduł</TableHead>
                <TableHead>Tryb</TableHead>
                <TableHead>Co to oznacza dla użytkownika</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(modes).map(([name, mode]) => {
                const description = describeModule(name);
                return (
                  <TableRow key={name}>
                    <TableCell>
                      <span className="font-medium">{description.label}</span>
                      <span className="block font-mono text-xs text-muted-foreground">
                        {name}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={mode === "real" ? "default" : "secondary"}>
                        {MODE_LABEL[mode]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {mode === "real" ? description.real : description.fake}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
