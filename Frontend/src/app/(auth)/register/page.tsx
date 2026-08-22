"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthCard } from "@/components/auth-card";
import { PhotoPicker } from "@/components/photo-picker";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/field";

const countries = [
  "India",
  "Japan",
  "Indonesia",
  "United Arab Emirates",
  "United Kingdom",
  "United States",
  "Other",
].map((name) => ({ label: name, value: name }));

const emptyForm = {
  firstName: "",
  lastName: "",
  username: "",
  password: "",
  email: "",
  phone: "",
  city: "",
  country: "",
  about: "",
};

type Form = typeof emptyForm;
type Errors = Partial<Record<keyof Form, string>>;

function validate(form: Form): Errors {
  const errors: Errors = {};

  if (!form.firstName.trim()) errors.firstName = "First name is required";
  if (!form.lastName.trim()) errors.lastName = "Last name is required";
  if (form.username.trim().length < 3)
    errors.username = "Pick a username with at least 3 characters";
  if (form.password.length < 6)
    errors.password = "Password must be at least 6 characters";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = "Enter a valid email address";
  if (!/^\+?[\d\s-]{10,15}$/.test(form.phone))
    errors.phone = "Enter a valid phone number";
  if (!form.city.trim()) errors.city = "City is required";
  if (!form.country) errors.country = "Select a country";

  return errors;
}

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState<Form>(emptyForm);
  const [photo, setPhoto] = useState<string | null>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);

  // Release the object URL of the previous preview whenever it is replaced.
  useEffect(() => {
    if (!photo) return;
    return () => URL.revokeObjectURL(photo);
  }, [photo]);

  function update<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handlePhotoChange(file: File | null) {
    setPhoto(file ? URL.createObjectURL(file) : null);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    router.push("/");
  }

  return (
    <AuthCard
      title="Create your account"
      subtitle="Tell us a little about you so we can tailor your trips."
      footer={{
        prompt: "Already have an account?",
        linkLabel: "Login",
        href: "/login",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <PhotoPicker
          name={`${form.firstName} ${form.lastName}`.trim() || "New traveller"}
          preview={photo}
          onChange={handlePhotoChange}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="First Name"
            autoComplete="given-name"
            value={form.firstName}
            onChange={(event) => update("firstName", event.target.value)}
            error={errors.firstName}
          />
          <Input
            label="Last Name"
            autoComplete="family-name"
            value={form.lastName}
            onChange={(event) => update("lastName", event.target.value)}
            error={errors.lastName}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Username"
            autoComplete="username"
            value={form.username}
            onChange={(event) => update("username", event.target.value)}
            error={errors.username}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            error={errors.password}
          />
        </div>

        <Input
          label="Email Address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={(event) => update("email", event.target.value)}
          error={errors.email}
        />

        <Input
          label="Phone Number"
          type="tel"
          autoComplete="tel"
          placeholder="+91 98765 43210"
          value={form.phone}
          onChange={(event) => update("phone", event.target.value)}
          error={errors.phone}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="City"
            autoComplete="address-level2"
            value={form.city}
            onChange={(event) => update("city", event.target.value)}
            error={errors.city}
          />
          <Select
            label="Country"
            options={countries}
            placeholder="Select a country"
            value={form.country}
            onChange={(event) => update("country", event.target.value)}
            error={errors.country}
          />
        </div>

        <Textarea
          label="Additional Information"
          placeholder="Favourite kind of trip, dietary needs, anything else we should know…"
          hint="Optional"
          value={form.about}
          onChange={(event) => update("about", event.target.value)}
        />

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthCard>
  );
}
