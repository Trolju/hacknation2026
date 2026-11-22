import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { apiErrorMessage } from "@/components/errorMessages";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import type { ApplicantType, Case } from "@/lib/types";

const CASE_NUMBER_PATTERN = /^[A-Z]{2,5}\.[A-Z]{1,4}\.[0-9]{1,6}\.[0-9]{1,9}\.[0-9]{4}$/;

const APPLICANT_LABEL: Record<ApplicantType, string> = {
  osoba_fizyczna: "Osoba fizyczna",
  organizacja: "Organizacja",
  media: "Media",
  inne: "Inne",
};

const schema = z.object({
  case_number: z
    .string()
    .trim()
    .min(1, "Numer sprawy jest wymagany.")
    .regex(
      CASE_NUMBER_PATTERN,
      "Format numeru: <komórka>.<dziennik>.<numer>.<rok>, np. BKS.IV.1431.12.2026.",
    ),
  subject: z
    .string()
    .trim()
    .min(1, "Temat wniosku jest wymagany.")
    .max(200, "Temat może mieć najwyżej 200 znaków."),
  applicant: z
    .string()
    .trim()
    .max(200, "Wnioskodawca może mieć najwyżej 200 znaków."),
  inflow_date: z.string().min(1, "Data wpływu jest wymagana."),
  handler_initials: z
    .string()
    .trim()
    .max(4, "Inicjały mają najwyżej 4 znaki.")
    .refine(
      (value) => value === "" || value.length >= 2,
      "Inicjały mają od 2 do 4 znaków.",
    ),
  applicant_type: z.enum(["osoba_fizyczna", "organizacja", "media", "inne"]),
  deadline: z.string(),
});

type FormValues = z.infer<typeof schema>;

function todayInputValue(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function emptyValues(): FormValues {
  return {
    case_number: "",
    subject: "",
    applicant: "",
    inflow_date: todayInputValue(),
    handler_initials: "",
    applicant_type: "inne",
    deadline: "",
  };
}

type NewCaseDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

/**
 * Szybka akcja „Nowy wniosek” z palety poleceń.
 *
 * Formularz zbiera tylko pola wymagane przez kontrakt (`CaseCreate`); termin
 * odpowiedzi wylicza backend z polityki 14 dni, jeśli pole zostanie puste.
 */
export function NewCaseDialog({ open, onOpenChange }: NewCaseDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: emptyValues(),
  });

  useEffect(() => {
    if (open) form.reset(emptyValues());
  }, [open, form]);

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      api.post<Case>("/cases", {
        case_number: values.case_number,
        subject: values.subject,
        applicant: values.applicant,
        inflow_date: values.inflow_date,
        handler_initials: values.handler_initials,
        applicant_type: values.applicant_type,
        deadline: values.deadline || null,
      }),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      toast.success("Wniosek dodany", { description: created.case_number });
      onOpenChange(false);
      navigate(`/kalendarz?case=${created.id}`);
    },
    onError: (error) => {
      toast.error("Nie udało się dodać wniosku", {
        description: apiErrorMessage(error),
      });
    },
  });

  const errors = form.formState.errors;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nowy wniosek</DialogTitle>
          <DialogDescription>
            Dodaj sprawę do kalendarza terminów. Termin odpowiedzi wyliczymy
            automatycznie, chyba że podasz własny.
          </DialogDescription>
        </DialogHeader>

        <form
          className="space-y-4"
          onSubmit={(event) => void form.handleSubmit((values) => create.mutate(values))(event)}
        >
          <div className="space-y-1.5">
            <Label htmlFor="new-case-number">Numer sprawy</Label>
            <Input
              id="new-case-number"
              placeholder="BKS.IV.1431.12.2026"
              autoComplete="off"
              aria-invalid={errors.case_number ? true : undefined}
              aria-describedby={
                errors.case_number ? "new-case-number-error" : undefined
              }
              {...form.register("case_number")}
            />
            {errors.case_number ? (
              <p id="new-case-number-error" className="text-xs text-destructive">
                {errors.case_number.message}
              </p>
            ) : null}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="new-case-subject">Temat wniosku</Label>
            <Input
              id="new-case-subject"
              placeholder="Krótki opis, np. Wynagrodzenia pracowników w 2025 r."
              autoComplete="off"
              aria-invalid={errors.subject ? true : undefined}
              aria-describedby={
                errors.subject ? "new-case-subject-error" : undefined
              }
              {...form.register("subject")}
            />
            {errors.subject ? (
              <p id="new-case-subject-error" className="text-xs text-destructive">
                {errors.subject.message}
              </p>
            ) : null}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="new-case-applicant-name">Wnioskodawca</Label>
            <Input
              id="new-case-applicant-name"
              placeholder="Nazwisko, nazwa organizacji albo e-mail"
              autoComplete="off"
              aria-invalid={errors.applicant ? true : undefined}
              aria-describedby={
                errors.applicant ? "new-case-applicant-name-error" : undefined
              }
              {...form.register("applicant")}
            />
            {errors.applicant ? (
              <p id="new-case-applicant-name-error" className="text-xs text-destructive">
                {errors.applicant.message}
              </p>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="new-case-inflow">Data wpływu</Label>
              <Input
                id="new-case-inflow"
                type="date"
                aria-invalid={errors.inflow_date ? true : undefined}
                {...form.register("inflow_date")}
              />
              {errors.inflow_date ? (
                <p className="text-xs text-destructive">
                  {errors.inflow_date.message}
                </p>
              ) : null}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="new-case-deadline">Termin odpowiedzi</Label>
              <Input
                id="new-case-deadline"
                type="date"
                {...form.register("deadline")}
              />
              <p className="text-xs text-muted-foreground">
                Puste pole oznacza termin wyliczony z 14 dni.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="new-case-initials">Inicjały osoby obsługującej</Label>
              <Input
                id="new-case-initials"
                placeholder="JK"
                maxLength={4}
                autoComplete="off"
                aria-invalid={errors.handler_initials ? true : undefined}
                {...form.register("handler_initials")}
              />
              {errors.handler_initials ? (
                <p className="text-xs text-destructive">
                  {errors.handler_initials.message}
                </p>
              ) : null}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="new-case-applicant">Typ wnioskodawcy</Label>
              <Select
                value={form.watch("applicant_type")}
                onValueChange={(value) =>
                  form.setValue("applicant_type", value as ApplicantType, {
                    shouldValidate: true,
                  })
                }
              >
                <SelectTrigger id="new-case-applicant">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(
                    Object.keys(APPLICANT_LABEL) as ApplicantType[]
                  ).map((value) => (
                    <SelectItem key={value} value={value}>
                      {APPLICANT_LABEL[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Anuluj
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : null}
              Dodaj wniosek
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
