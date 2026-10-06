import type { ReactNode } from "react";
import { ArrowUpRight, Check, X, LoaderCircle } from "lucide-react";
import { title, type Data } from "../api";
export function Badge({ value }: { value: string }) {
  const fail = /FAIL|CANCEL|CLOSED|HIGH|REPLAN|DEFECT|DISPUTED/.test(value);
  return (
    <span
      className={`badge ${fail ? "danger" : /PASS|DELIVER|AVAILABLE|LOW|OPEN|SETTLED/.test(value) ? "success" : "neutral"}`}
    >
      <i />
      {title(value)}
    </span>
  );
}
export function Panel({
  title: heading,
  eyebrow,
  children,
  action,
  className = "",
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2>{heading}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: ReactNode;
  note?: string;
}) {
  return (
    <div className="stat">
      <div className="stat-label">
        {label}
        <ArrowUpRight size={15} />
      </div>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}
export function Loading() {
  return (
    <div className="loading">
      <LoaderCircle size={24} className="spin" />
      Loading workspace…
    </div>
  );
}
export function Progress({ value }: { value: number }) {
  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuenow={Math.round(value * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span style={{ width: `${Math.min(100, value * 100)}%` }} />
    </div>
  );
}
export function CheckItem({
  passed,
  children,
}: {
  passed: boolean;
  children: ReactNode;
}) {
  return (
    <div className={`check-item ${passed ? "" : "failed"}`}>
      {passed ? <Check size={15} /> : <X size={15} />}
      <span>{children}</span>
    </div>
  );
}
export function TerminalTable({ data }: { data: Data }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Terminal</th>
            <th>Equipment</th>
            <th>Storage</th>
            <th>Approach depth</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.terminals.map((t: Data) => (
            <tr key={t.id}>
              <td>
                <strong>{t.name}</strong>
                <small>Synthetic capabilities · {t.source_date}</small>
              </td>
              <td>
                {t.capability.crane_available ? "Crane" : ""} ·{" "}
                {t.capability.forklift_available ? "Forklift" : ""}
              </td>
              <td>{t.capability.available_storage} t</td>
              <td>{t.capability.approach_channel} m</td>
              <td>
                <Badge value={t.capability.operational_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
