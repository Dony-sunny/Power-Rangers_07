import { useState, useEffect } from "react";
import { Mic } from "lucide-react";
import { api, type Data, money, date, title } from "../api";
import { Panel, Stat, Badge, Empty, Progress } from "./UI";
import RouteMap from "./RouteMap";

export default function Operator({
  data,
  role,
  setView,
}: {
  data: Data;
  role: string;
  setView: (view: string) => void;
}) {
  const [vesselId, setVesselId] = useState(data.vessels[0]?.id || ""),
    [opportunities, setOpportunities] = useState<Data | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    if (vesselId)
      api(`/vessels/${vesselId}/opportunities`, role)
        .then(setOpportunities)
        .catch((e) => setError(e.message));
  }, [vesselId, role, data.availability.length]);
  const vessel = data.vessels.find((v: Data) => v.id === vesselId),
    booked = data.shipments
      .filter(
        (s: Data) =>
          s.booking.vessel_id === vesselId &&
          !["CANCELLED", "FAILED", "DELIVERED"].includes(s.booking.status),
      )
      .reduce((n: number, s: Data) => n + s.cargo.weight_tonnes, 0),
    pool = opportunities?.pool;
  return (
    <>
      {error && <div className="alert error">{error}</div>}
      <div className="stats-row">
        <Stat
          label="Available vessel capacity"
          value={`${Math.max(0, (vessel?.max_capacity_tonnes || 0) - booked)} t`}
          note={vessel?.name}
        />
        <Stat
          label="Booked cargo"
          value={`${booked} t`}
          note="Application bookings"
        />
        <Stat
          label="Projected pooled utilization"
          value={pool ? `${pool.utilization_after_pct}%` : "—"}
          note="Pending cargo-owner approval"
        />
        <Stat
          label="Potential additional freight"
          value={money(pool?.additional_revenue)}
          note="Calculated from compatible loads"
        />
      </div>
      <div className="two-columns">
        <Panel
          title="Your earning opportunities"
          action={
            <select
              aria-label="Operator vessel"
              value={vesselId}
              onChange={(e) => setVesselId(e.target.value)}
            >
              {data.vessels.map((v: Data) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          }
        >
          {(opportunities?.cargo || []).map((c: Data) => (
            <div className="shipment-card" key={c.id}>
              <div className="shipment-card-head">
                <h3>
                  {title(c.cargo_type)} · {c.weight_tonnes} t
                </h3>
                <Badge value="FEASIBILITY_PASS" />
              </div>
              <p>
                {c.origin} → {c.destination}
              </p>
              <strong>
                {money(c.estimated_freight_revenue)} estimated water freight
              </strong>
              <small>
                ETA {date(c.eta)} · Derived from your rate and route distance
              </small>
            </div>
          ))}
          {!opportunities?.cargo.length && (
            <Empty>No unbooked cargo fits this vessel.</Empty>
          )}
          {pool && (
            <div className="pool-result">
              <div>
                <strong>{pool.total_tonnes} t pooled</strong>
                <span>
                  {pool.utilization_before_pct}% → {pool.utilization_after_pct}%
                </span>
              </div>
              <Progress value={pool.utilization_after_pct / 100} />
              <small>
                OR-Tools {pool.solver_status} · preview, no reservation
              </small>
            </div>
          )}
        </Panel>
        <div>
          <Panel title="Your fleet along the corridor">
            <RouteMap data={data} />
            <div className="shipment-actions" style={{ padding: 18 }}>
              <button
                className="button primary"
                onClick={() => setView("voice")}
              >
                <Mic size={15} />
                Speak Malayalam to list capacity
              </button>
              <button className="button" onClick={() => setView("fleet")}>
                Manage fleet
              </button>
            </div>
          </Panel>
          {opportunities &&
            opportunities.backhaul?.opportunities?.length > 0 && (
              <Panel title="Return-load opportunity">
                <div className="backhaul-result">
                  <Badge value="RETURN_LOAD_FOUND" />
                  <h3>
                    {opportunities.backhaul.opportunities[0].cargo_type} ·{" "}
                    {opportunities.backhaul.opportunities[0].weight_tonnes} t
                  </h3>
                  <p>
                    {opportunities.backhaul.opportunities[0].origin} →{" "}
                    {opportunities.backhaul.opportunities[0].destination}
                  </p>
                  <strong>
                    {money(opportunities.backhaul.opportunities[0].revenue)}{" "}
                    potential freight revenue
                  </strong>
                  <small>
                    Confirmed return availability and turnaround checked.
                  </small>
                </div>
              </Panel>
            )}
        </div>
      </div>
      <Panel title="Operator reliability & trust">
        <div className="detail-grid">
          <label>
            Reliability
            <strong>
              {Math.round((vessel?.reliability_score || 0) * 100)}%
            </strong>
          </label>
          <label>
            Completed voyages
            <strong>{vessel?.trust_metrics?.completed_voyages ?? "—"}</strong>
          </label>
          <label>
            Cancellation percentage
            <strong>{vessel?.trust_metrics?.cancellation_pct ?? "—"}%</strong>
          </label>
          <label>
            Insurance
            <strong>
              {data.certificates.find(
                (c: Data) => c.vessel_id === vesselId && c.kind === "INSURANCE",
              )
                ? "Certificate recorded"
                : "Not recorded"}
            </strong>
          </label>
          <label>
            Compliance<strong>{vessel?.compliance_status}</strong>
          </label>
          <label>
            Source<strong>Synthetic demo history</strong>
          </label>
        </div>
      </Panel>
    </>
  );
}
