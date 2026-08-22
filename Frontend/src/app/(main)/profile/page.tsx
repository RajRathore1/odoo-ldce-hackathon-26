"use client";

import { useState } from "react";
import { PhotoPicker } from "@/components/photo-picker";
import { SectionHeader } from "@/components/section-header";
import { TripCard } from "@/components/trip-card";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/field";
import { trips } from "@/lib/mock-data";

const countries = [
  "India",
  "Japan",
  "Indonesia",
  "United Arab Emirates",
  "United Kingdom",
  "United States",
  "Other",
].map((name) => ({ label: name, value: name }));

const initialProfile = {
  firstName: "Abhishek",
  lastName: "Singh",
  username: "abhishek.s",
  email: "abhishek.singh@example.com",
  phone: "+91 98765 43210",
  city: "Ahmedabad",
  country: "India",
  about: "",
};

type Profile = typeof initialProfile;

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(initialProfile);
  const [photo, setPhoto] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile((current) => ({ ...current, [key]: value }));
    setSaved(false);
  }

  function handlePhotoChange(file: File | null) {
    setPhoto(file ? URL.createObjectURL(file) : null);
    setSaved(false);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(true);
  }

  const preplanned = trips.filter((trip) => trip.status === "upcoming");
  const previous = trips.filter((trip) => trip.status !== "upcoming");

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Your profile
        </h1>
        <p className="mt-2 text-text-muted">
          Keep your details current so trip plans and confirmations reach the
          right place.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8"
      >
        <PhotoPicker
          name={`${profile.firstName} ${profile.lastName}`.trim() || "Traveller"}
          preview={photo}
          onChange={handlePhotoChange}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="First Name"
            autoComplete="given-name"
            value={profile.firstName}
            onChange={(event) => update("firstName", event.target.value)}
          />
          <Input
            label="Last Name"
            autoComplete="family-name"
            value={profile.lastName}
            onChange={(event) => update("lastName", event.target.value)}
          />
        </div>

        <Input
          label="Username"
          autoComplete="username"
          value={profile.username}
          onChange={(event) => update("username", event.target.value)}
        />

        <Input
          label="Email Address"
          type="email"
          autoComplete="email"
          value={profile.email}
          onChange={(event) => update("email", event.target.value)}
        />

        <Input
          label="Phone Number"
          type="tel"
          autoComplete="tel"
          value={profile.phone}
          onChange={(event) => update("phone", event.target.value)}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="City"
            autoComplete="address-level2"
            value={profile.city}
            onChange={(event) => update("city", event.target.value)}
          />
          <Select
            label="Country"
            options={countries}
            value={profile.country}
            onChange={(event) => update("country", event.target.value)}
          />
        </div>

        <Textarea
          label="Additional Information"
          placeholder="Favourite kind of trip, dietary needs, anything else we should know…"
          hint="Optional"
          value={profile.about}
          onChange={(event) => update("about", event.target.value)}
        />

        <div className="flex items-center justify-end gap-3 border-t border-border pt-6">
          {saved && (
            <span className="text-sm font-medium text-success">Saved</span>
          )}
          <Button type="submit">Save changes</Button>
        </div>
      </form>

      <section>
        <SectionHeader
          title="Preplanned trips"
          description="Trips you've already locked dates in for."
        />
        {preplanned.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {preplanned.map((trip) => (
              <TripCard key={trip.id} trip={trip} href={`/trips/${trip.id}`} />
            ))}
          </div>
        ) : (
          <EmptyState message="No preplanned trips yet." />
        )}
      </section>

      <section>
        <SectionHeader
          title="Previous trips"
          description="Trips you've completed or are on right now."
        />
        {previous.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {previous.map((trip) => (
              <TripCard key={trip.id} trip={trip} href={`/trips/${trip.id}`} />
            ))}
          </div>
        ) : (
          <EmptyState message="No previous trips yet." />
        )}
      </section>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
      {message}
    </p>
  );
}
