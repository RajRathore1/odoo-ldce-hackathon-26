"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { AdminDashboard } from "@/components/admin-dashboard";
import { AdminShell } from "@/components/admin-shell";
import { isAdminAuthed } from "@/lib/admin-auth";

function subscribe() {
  return () => {};
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const authed = useSyncExternalStore(subscribe, isAdminAuthed, () => false);

  useEffect(() => {
    if (!authed) router.replace("/login");
  }, [authed, router]);

  if (!authed) return null;

  return (
    <AdminShell>
      <AdminDashboard />
    </AdminShell>
  );
}
