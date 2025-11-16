export const apiBase = "/api";

export async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(`${apiBase}${url}`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(`${apiBase}${url}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const parsed = JSON.parse(text);
      throw new Error(parsed.detail || text);
    } catch {
      throw new Error(text || `HTTP ${res.status}`);
    }
  }
  return (await res.json()) as T;
}
