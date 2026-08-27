export function normalizeRunnerUrl(value: string) {
  return value.trim().replace(/\/+$/, "");
}

export function parsePhoneNumbers(value: string) {
  return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
}
