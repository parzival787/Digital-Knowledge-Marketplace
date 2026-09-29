export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options, credentials: "include", cache: "no-store",
    headers: { "X-DKM-Request": "1", ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}), ...options.headers },
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = result.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((e: { msg: string }) => e.msg).join("; ") : "Service unavailable. Please retry.");
  }
  return result as T;
}
