import { LogIn, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { toast } from "sonner";

import { apiErrorMessage } from "@/components/errorMessages";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useAuthUsers, useLogin } from "./api";
import { TEXT, roleLabel } from "./i18n";
import { useAuth } from "./useAuth";

export default function LoginPage() {
  const { signIn } = useAuth();
  const users = useAuthUsers();
  const login = useLogin();
  const [initials, setInitials] = useState("");
  const [pin, setPin] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!initials) {
      toast.error(TEXT.initials);
      return;
    }
    login.mutate(
      { initials, pin },
      {
        onSuccess: (session) => signIn(session),
        onError: (error) => {
          toast.error(TEXT.failed, { description: apiErrorMessage(error) });
        },
      },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            {TEXT.demo}
          </div>
          <CardTitle className="text-2xl">{TEXT.title}</CardTitle>
          <CardDescription>{TEXT.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="login-user">{TEXT.initials}</Label>
              <Select value={initials} onValueChange={setInitials}>
                <SelectTrigger id="login-user">
                  <SelectValue placeholder={TEXT.initials} />
                </SelectTrigger>
                <SelectContent>
                  {(users.data ?? []).map((user) => (
                    <SelectItem key={user.initials} value={user.initials}>
                      {user.initials} — {user.name} ({roleLabel(user.role)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {users.isError && (
                <p className="text-xs text-destructive">{TEXT.usersFailed}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="login-pin">{TEXT.pin}</Label>
              <Input
                id="login-pin"
                type="password"
                inputMode="numeric"
                autoComplete="current-password"
                value={pin}
                onChange={(event) => setPin(event.target.value)}
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">{TEXT.pinHint}</p>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={login.isPending || !initials || pin.length < 4}
            >
              <LogIn />
              {login.isPending ? TEXT.submitting : TEXT.submit}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
