"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AuthCard } from "@/components/auth-card";
import { FormAlert } from "@/components/form-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { useAuth } from "@/components/auth-provider";
import { ApiError } from "@/lib/api/envelope";

type Errors = Partial<Record<"email" | "password", string>>;

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [alert, setAlert] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: Errors = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      nextErrors.email = "Enter a valid email address";
    if (!password) nextErrors.password = "Password is required";

    setErrors(nextErrors);
    setAlert(null);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);

    try {
      await signIn(email, password);
      router.replace(params.get("next") ?? "/");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
        setErrors(error.fields);
      } else {
        setAlert("Could not reach the server. Try again in a moment.");
      }
      setSubmitting(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Log in to pick up where your itinerary left off."
      footer={{
        prompt: "New to GlobeTrotter?",
        linkLabel: "Create an account",
        href: "/register",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <FormAlert message={alert} />

        <Input
          label="Email Address"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={errors.email}
        />

        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="........"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
        />

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-text-muted">
            <input
              type="checkbox"
              className="size-4 rounded border-border accent-primary"
            />
            Remember me
          </label>
          <button
            type="button"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Forgot password?
          </button>
        </div>

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Logging in..." : "Login"}
        </Button>
      </form>
    </AuthCard>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
