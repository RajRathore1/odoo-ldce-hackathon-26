"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthCard } from "@/components/auth-card";
import { FormAlert } from "@/components/form-alert";
import { PhotoPicker } from "@/components/photo-picker";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/field";
import { useAuth } from "@/components/auth-provider";
import { ApiError } from "@/lib/api/envelope";

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
  email: "",
  password: "",
  confirmPassword: "",
  phone: "",
  city: "",
  country: "",
  about: "",
};

type Form = typeof emptyForm;
type Errors = Partial<Record<keyof Form, string>> & { form?: string };

// Field names the backend rejects with, mapped onto our form state.
const backendFields: Record<string, keyof Form> = {
  email: "email",
  password: "password",
  confirm_password: "confirmPassword",
  first_name: "firstName",
  last_name: "lastName",
  phone_number: "phone",
  additional_info: "about",
};

function validate(form: Form): Errors {
  const errors: Errors = {};

  if (!form.firstName.trim()) errors.firstName = "First name is required";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = "Enter a valid email address";
  if (form.password.length < 8)
    errors.password = "Password must be at least 8 characters";
  if (form.confirmPassword !== form.password)
    errors.confirmPassword = "Passwords do not match";
  if (form.phone && !/^\+?[\d\s-]{10,15}$/.test(form.phone))
    errors.phone = "Enter a valid phone number";

  return errors;
}

export default function RegisterPage() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [form, setForm] = useState<Form>(emptyForm);
  const [photo, setPhoto] = useState<string | null>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [alert, setAlert] = useState<string | null>(null);
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

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validate(form);
    setErrors(nextErrors);
    setAlert(null);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);

    try {
      await signUp({
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
        first_name: form.firstName,
        last_name: form.lastName,
        phone_number: form.phone,
        additional_info: form.about,
      });
      router.replace("/");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
        const mapped: Errors = {};
        for (const [key, message] of Object.entries(error.fields)) {
          const target = backendFields[key];
          if (target) mapped[target] = message;
        }
        setErrors(mapped);
      } else {
        setAlert("Could not reach the server. Try again in a moment.");
      }
      setSubmitting(false);
    }
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
        <FormAlert message={alert} />

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

        <Input
          label="Email Address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={(event) => update("email", event.target.value)}
          error={errors.email}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            error={errors.password}
          />
          <Input
            label="Confirm Password"
            type="password"
            autoComplete="new-password"
            value={form.confirmPassword}
            onChange={(event) => update("confirmPassword", event.target.value)}
            error={errors.confirmPassword}
          />
        </div>

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
            hint="Saved once the locations service is live"
            value={form.city}
            onChange={(event) => update("city", event.target.value)}
          />
          <Select
            label="Country"
            options={countries}
            placeholder="Select a country"
            hint="Saved once the locations service is live"
            value={form.country}
            onChange={(event) => update("country", event.target.value)}
          />
        </div>

        <Textarea
          label="Additional Information"
          placeholder="Favourite kind of trip, dietary needs, anything else we should know"
          hint="Optional"
          value={form.about}
          onChange={(event) => update("about", event.target.value)}
        />

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </Button>
      </form>
    </AuthCard>
  );
}
