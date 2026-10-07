export type Data = Record<string, any>;
export interface Cargo {
  id: string;
  cargo_type: string;
  weight_tonnes: number;
  volume_m3: number | null;
  packaging: string;
  origin: string;
  destination: string;
  ready_time: string;
  delivery_deadline: string;
  status: string;
  first_mile_required: boolean;
  last_mile_required: boolean;
  consolidation_allowed: boolean;
  [key: string]: any;
}
export async function api<T = Data>(
  path: string,
  role: string,
  body?: unknown,
  method?: string,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: method || (body ? "POST" : "GET"),
    headers: {
      "X-Demo-Role": role,
      ...(role === "operator" && localStorage.getItem("jalayatra-operator-user")
        ? { "X-Demo-User": localStorage.getItem("jalayatra-operator-user")! }
        : {}),
      ...(sessionStorage.getItem("jalayatra-token")
        ? {
            Authorization: `Bearer ${sessionStorage.getItem("jalayatra-token")}`,
          }
        : {}),
      ...(body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body: body
      ? body instanceof FormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });
  const result = await response.json();
  if (!response.ok) {
    const detail = result.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((d: Data) => `${d.loc?.slice(1).join(".")}: ${d.msg}`)
              .join("; ")
          : detail?.message
            ? `${detail.message} ${(detail.reasons || []).join(" ")}`
            : "The request failed. Please retry.",
    );
  }
  return result;
}
export async function download(path: string, role: string, filename: string) {
  const response = await fetch(`/api${path}`, {
    headers: {
      "X-Demo-Role": role,
      ...(sessionStorage.getItem("jalayatra-token")
        ? {
            Authorization: `Bearer ${sessionStorage.getItem("jalayatra-token")}`,
          }
        : {}),
    },
  });
  if (!response.ok) throw new Error("Download unavailable or unauthorized.");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const money = (n: number | null | undefined) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(n);
export const date = (value: string | undefined) =>
  value
    ? new Date(value).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
export const title = (value: string) =>
  value
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/^./, (c) => c.toUpperCase());
export type Act = (
  task: () => Promise<unknown>,
  message?: string,
) => Promise<void>;
