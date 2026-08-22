export type Envelope<T> = {
  success: boolean;
  message: string | null;
  data: T;
  errors?: {
    fields?: Record<string, unknown>;
    detail?: string;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly fields: Record<string, string>;

  constructor(
    status: number,
    message: string,
    fields: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

// The backend wraps everything in {success, message, data} and puts validation
// problems under errors.fields as arrays. Flatten to one message per field so
// forms can bind straight to it.
export async function readEnvelope<T>(response: Response): Promise<T> {
  // DELETE answers 204 with no body at all, which is a success, not a parse
  // failure.
  if (response.status === 204) return null as T;

  let body: Envelope<T> | null = null;

  try {
    body = (await response.json()) as Envelope<T>;
  } catch {
    body = null;
  }

  if (!response.ok || !body?.success) {
    throw new ApiError(
      response.status,
      body?.message ?? `Request failed (${response.status})`,
      flattenFieldErrors(body?.errors?.fields),
    );
  }

  return body.data;
}

function flattenFieldErrors(fields: Record<string, unknown> | undefined) {
  const flat: Record<string, string> = {};
  if (!fields) return flat;

  for (const [key, value] of Object.entries(fields)) {
    if (Array.isArray(value) && typeof value[0] === "string") {
      flat[key] = value[0];
    } else if (typeof value === "string") {
      flat[key] = value;
    }
  }

  return flat;
}
