import { redirect } from "next/navigation";
import { GlobalTrotterNavbar } from "@/components/navbar";
import { getCurrentUser } from "@/lib/api/session";

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();

  // proxy.ts already gates these routes; this catches a refresh token that the
  // backend has since rejected.
  if (!user) redirect("/login");

  return (
    <>
      <GlobalTrotterNavbar
        user={{
          name: user.full_name || user.first_name || user.email,
          avatar: user.avatar,
        }}
      />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>
    </>
  );
}
