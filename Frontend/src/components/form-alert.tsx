export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null;

  return (
    <p
      role="alert"
      className="rounded-xl border border-danger/25 bg-danger/8 px-3.5 py-2.5 text-sm text-danger"
    >
      {message}
    </p>
  );
}
