"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";

type Errors = Partial<Record<"username" | "password", string>>;

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: Errors = {};
    if (!username.trim()) nextErrors.username = "Username is required";
    if (password.length < 6)
      nextErrors.password = "Password must be at least 6 characters";

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    router.push("/");
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
        <Input
          label="Username"
          name="username"
          autoComplete="username"
          placeholder="abhishek.s"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          error={errors.username}
        />

        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
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
          {submitting ? "Logging in…" : "Login"}
        </Button>
      </form>
    </AuthCard>
  );
}
