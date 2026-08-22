"use client";

import { useEffect, useState } from "react";
import { FormAlert } from "@/components/form-alert";
import { PhotoPicker } from "@/components/photo-picker";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/field";
import { SubmitError, postJson } from "@/lib/api/browser";
import type { AuthUser } from "@/lib/api/types";
import type { SelectOption } from "@/lib/types";

type ProfileFormProps = {
  user: AuthUser;
  countries: SelectOption[];
  cities: SelectOption[];
};

// Backend field names mapped onto our inputs.
const backendFields: Record<string, string> = {
  first_name: "firstName",
  last_name: "lastName",
  phone_number: "phone",
  additional_info: "about",
  city: "city",
  country: "country",
};

export function ProfileForm({ user, countries, cities }: ProfileFormProps) {
  const [profile, setProfile] = useState({
    firstName: user.first_name,
    lastName: user.last_name,
    phone: user.phone_number,
    city: user.city ? String(user.city.id) : "",
    country: user.country ? String(user.country.id) : "",
    about: user.additional_info,
  });
  const [photo, setPhoto] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [alert, setAlert] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!photo) return;
    return () => URL.revokeObjectURL(photo);
  }, [photo]);

  function update(key: keyof typeof profile, value: string) {
    setProfile((current) => ({ ...current, [key]: value }));
    setSaved(false);
  }

  async function handlePhotoChange(file: File | null) {
    setPhoto(file ? URL.createObjectURL(file) : null);
    setSaved(false);
    if (!file) return;

    const form = new FormData();
    form.append("avatar", file);

    try {
      const response = await fetch("/api/profile", {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setAlert(body?.message ?? "Could not upload that photo.");
      }
    } catch {
      setAlert("Could not upload that photo.");
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAlert(null);
    setErrors({});
    setSaving(true);

    try {
      await postJson("/api/profile", {
        first_name: profile.firstName,
        last_name: profile.lastName,
        phone_number: profile.phone,
        additional_info: profile.about,
        city: profile.city ? Number(profile.city) : null,
        country: profile.country ? Number(profile.country) : null,
      });
      setSaved(true);
    } catch (error) {
      if (error instanceof SubmitError) {
        setAlert(error.message);
        const mapped: Record<string, string> = {};
        for (const [key, message] of Object.entries(error.fields)) {
          const target = backendFields[key];
          if (target) mapped[target] = message;
        }
        setErrors(mapped);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8"
    >
      <FormAlert message={alert} />

      <PhotoPicker
        name={`${profile.firstName} ${profile.lastName}`.trim() || "Traveller"}
        preview={photo ?? user.avatar}
        onChange={handlePhotoChange}
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="First Name"
          autoComplete="given-name"
          value={profile.firstName}
          onChange={(event) => update("firstName", event.target.value)}
          error={errors.firstName}
        />
        <Input
          label="Last Name"
          autoComplete="family-name"
          value={profile.lastName}
          onChange={(event) => update("lastName", event.target.value)}
          error={errors.lastName}
        />
      </div>

      <Input
        label="Email Address"
        type="email"
        value={user.email}
        hint="Email cannot be changed here"
        disabled
        readOnly
      />

      <Input
        label="Phone Number"
        type="tel"
        autoComplete="tel"
        value={profile.phone}
        onChange={(event) => update("phone", event.target.value)}
        error={errors.phone}
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          label="City"
          options={cities}
          placeholder="Select a city"
          value={profile.city}
          onChange={(event) => update("city", event.target.value)}
          error={errors.city}
        />
        <Select
          label="Country"
          options={countries}
          placeholder="Select a country"
          value={profile.country}
          onChange={(event) => update("country", event.target.value)}
          error={errors.country}
        />
      </div>

      <Textarea
        label="Additional Information"
        placeholder="Favourite kind of trip, dietary needs, anything else we should know"
        hint="Optional"
        value={profile.about}
        onChange={(event) => update("about", event.target.value)}
        error={errors.about}
      />

      <div className="flex items-center justify-end gap-3 border-t border-border pt-6">
        {saved && (
          <span className="text-sm font-medium text-success">Saved</span>
        )}
        <Button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
