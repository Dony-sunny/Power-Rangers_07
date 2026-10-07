import { useEffect, useState } from "react";
import { api, type Data, type Act, money } from "../api";
import { Panel, Badge, Empty, Stat } from "./UI";

export function RateBenchmark({
  cargoId,
  vesselId,
  role,
}: {
  cargoId: string;
  vesselId: string;
  role: string;
}) {
  const [result, setResult] = useState<Data | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api(`/cargo/${cargoId}/rate-benchmark?vessel_id=${vesselId}`, role)
      .then(setResult)
      .catch((e) => setError(e.message));
  }, [cargoId, vesselId, role]);
  return (
    <Panel title="Comparable demo freight rates">
      <div className="form-content">
        {error && <div className="alert error">{error}</div>}
        {result && (
          <>
            <p>
              {result.corridor} · {result.cargo_class} ·{" "}
              {result.weight_band_tonnes.join("–")} t · {result.lookback_days}{" "}
              days
            </p>
            <div className="metric-summary">
              <span>
                Current delivered rate: {money(result.current_rate_per_tonne)} /
                t
              </span>
              <span>
                Comparable range:{" "}
                {result.range_per_tonne
                  ? result.range_per_tonne
                      .map((n: number) => money(n))
                      .join(" – ")
                  : "Insufficient history"}
              </span>
              <span>Sample size: {result.sample_size} prototype movements</span>
              <Badge value={result.status} />
            </div>
            <p>{result.source}</p>
            <small>{result.sources.join("; ")}</small>
            <button
              className="button small"
              onClick={() =>
                api(`/cargo/${cargoId}/reject-quote`, role, {})
                  .then(() =>
                    setError(
                      "Price rejection recorded in demand intelligence.",
                    ),
                  )
                  .catch((e) => setError(e.message))
              }
            >
              Record price rejection
            </button>
          </>
        )}
      </div>
    </Panel>
  );
}

export default function NetworkIntelligence({
  role,
  act,
  busy,
}: {
  role: string;
  act: Act;
  busy: boolean;
}) {
  const [corridors, setCorridors] = useState<Data | null>(null),
    [failed, setFailed] = useState<Data | null>(null),
    [analysis, setAnalysis] = useState<Data | null>(null),
    [file, setFile] = useState<File | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/intelligence/corridors", role)
      .then(setCorridors)
      .catch((e) => setError(e.message));
    if (["government", "network", "control", "admin"].includes(role))
      api("/intelligence/failed-demand", role)
        .then(setFailed)
        .catch((e) => setError(e.message));
  }, [role]);
  return (
    <>
      {error && <div className="alert error">{error}</div>}
      <Panel title="Corridor reliability from recorded trips">
        {corridors?.corridors.map((r: Data) => (
          <div className="shipment-card" key={r.corridor}>
            <h3>{r.corridor}</h3>
            <p>
              Sample size: {r.sample_size} completed voyages ·{" "}
              {r.history_status}
            </p>
            <div className="metric-summary">
              <span>
                Median recorded transit: {r.median_transit_hours ?? "—"} h
              </span>
              <span>
                Terminal wait: {r.average_terminal_wait_hours ?? "—"} h
              </span>
              <span>On-time: {r.on_time_pct ?? "—"}%</span>
              <span>Cancelled: {r.cancellation_pct}%</span>
              <span>Recoveries: {r.recovery_frequency_pct}%</span>
              <span>Disruptions: {r.route_disruption_pct}%</span>
              <span>
                Reliability score:{" "}
                {r.reliability_score ?? "Insufficient history"}
              </span>
            </div>
            <small>{r.source}</small>
          </div>
        ))}
        {!corridors?.corridors.length && (
          <Empty>
            No recorded voyage history. Scores require at least five completed
            voyages.
          </Empty>
        )}
      </Panel>
      {failed && (
        <Panel title="Failed-demand and market gaps">
          <Stat
            label="Unique unserved demand"
            value={`${failed.unserved_tonnes} t`}
          />
          {failed.corridors.map((r: Data) => (
            <div className="shipment-card" key={r.corridor}>
              <h3>{r.corridor}</h3>
              <p>
                {r.tonnes} t · {r.cargo_count} requests · {r.search_frequency}{" "}
                search events
              </p>
              <div className="metric-summary">
                {Object.entries(r.reasons).map(([reason, value]) => (
                  <span key={reason}>
                    {reason.replaceAll("_", " ")}: {(value as Data).tonnes} t
                  </span>
                ))}
              </div>
            </div>
          ))}
          <small>{failed.source}</small>
        </Panel>
      )}
      {["government", "network", "control", "admin", "shipper"].includes(
        role,
      ) && (
        <Panel
          title="Potential modal-shift opportunity"
          eyebrow="CSV/XLSX ROAD HISTORY · CURRENT DEMO SNAPSHOT"
        >
          <div className="form-content">
            <label className="field">
              Historical shipment file
              <input
                type="file"
                aria-label="Road history spreadsheet"
                accept=".csv,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
            <button
              className="button primary"
              disabled={busy || !file}
              onClick={() =>
                act(async () => {
                  const form = new FormData();
                  form.append("file", file!);
                  setAnalysis(
                    await api("/intelligence/modal-shift/upload", role, form),
                  );
                }, "Historical shipments analyzed as potential opportunities.")
              }
            >
              Analyze road-history opportunity
            </button>
            {analysis && (
              <>
                <div className="stats-row">
                  <Stat
                    label="Analyzed shipments"
                    value={analysis.total_shipments_analyzed}
                  />
                  <Stat
                    label="Candidate tonnes"
                    value={`${analysis.candidate_tonnes} t`}
                  />
                  <Stat
                    label="Potential cost difference"
                    value={money(analysis.estimated_cost_difference)}
                  />
                  <Stat
                    label="Estimated CO₂ difference"
                    value={`${analysis.estimated_co2_difference_kg} kg`}
                  />
                </div>
                {analysis.rows.map((r: Data) => (
                  <div className="shipment-card" key={r.row}>
                    <h3>
                      {r.origin} → {r.destination} · {r.weight_tonnes} t
                    </h3>
                    <Badge value={r.suitability} />
                    <p>{r.reasons.join("; ")}</p>
                  </div>
                ))}
                <small>{analysis.source}</small>
                {analysis.invalid_rows.length > 0 && (
                  <p>
                    {analysis.invalid_rows.length} invalid rows excluded and
                    listed for review.
                  </p>
                )}
              </>
            )}
          </div>
        </Panel>
      )}
    </>
  );
}
