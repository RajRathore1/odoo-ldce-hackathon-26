/**
 * Repair text the backend sent as UTF-8 bytes read back as Latin-1, which is
 * why city names arrive looking like "Ile-de-France" with stray accents and
 * flag emoji come through as four garbled characters.
 *
 * Only strings that are entirely in the Latin-1 range are worth trying, and an
 * invalid byte sequence means the guess was wrong, so the original is kept.
 */
export function decodeText(value: string) {
  if (!value) return value;

  let suspicious = false;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code > 255) return value;
    if (code > 127) suspicious = true;
  }

  if (!suspicious) return value;

  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(
      Uint8Array.from(value, (char) => char.charCodeAt(0)),
    );
  } catch {
    return value;
  }
}
