const root = process.env.NEXT_SERVER_PUBLIC_URL;

export function apiUrl(path: string) {
  if (!root) {
    throw new Error("NEXT_SERVER_PUBLIC_URL is not set - check Frontend/.env");
  }

  // Every backend route needs its trailing slash, see API.md section 1.
  return `${root.replace(/\/+$/, "")}/api/v1${path}`;
}
