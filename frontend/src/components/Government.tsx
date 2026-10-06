import { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { api, type Data, money } from "../api";
import { Panel, Stat, Badge, Empty } from "./UI";
import RouteMap from "./RouteMap";

export default function Government({
  data,
  role,
  view,
}: {
  data: Data;
  role: string;
  view: string;
}) {
  const [metrics, setMetrics] = useState<Data | null>(null),
    [modal, setModal] = useState<Data | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/impact", role)
      .then(setMetrics)
      .catch((e) => setError(e.message));
    if (view === "intelligence")
      api("/intelligence/modal-shift", role)
        .then(setModal)
        .catch((e) => setError(e.message));
  }, [role, view, data.shipments.length]);
  if (error) return <div className="alert error">{error}</div>;
  if (!metrics)
    return <Empty>Calculating booking-derived network metrics…</Empty>;
  return (
    <>
      <div className="stats-row">
        <Stat
          label="Cargo selected for water"
          value={`${metrics.tonnes_shifted} t`}
          note={`${metrics.completed_tonnes_shifted} t completed`}
        />
        <Stat
          label="Potential truck trips avoided"
          value={metrics.truck_trips_potentially_avoided}
          note="20-tonne prototype truck capacity"
        />
        <Stat
          label="Estimated CO₂ avoided"
          value={`${metrics.co2_avoided_kg} kg`}
          note="Prototype emission factors"
        />
        <Stat
          label="Estimated cost savings"
          value={money(metrics.cost_savings)}
          note="Versus full road baseline"
        />
      </div>
      {metrics.flood_simulated && (
        <div className="alert">
          Simulated resilience mode: road unavailable, unbooked cargo marked
          critical. No live emergency feed.
        </div>
      )}
      <div className="two-columns">
        <Panel
          title="Where cargo demand meets the waterway"
          eyebrow="DEMO DEMAND HEATMAP"
        >
          <RouteMap data={data} heat />
          <p className="provenance-mini">
            Circle size follows platform request tonnage. Approximate geography;
            no live government feed.
          </p>
        </Panel>
        <Panel title="Demand served, demand still waiting">
          <div className="metric-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={metrics.corridors}
                margin={{ left: 0, right: 10, bottom: 10 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e5ede0"
                />
                <XAxis dataKey="corridor" tick={{ fontSize: 8 }} interval={0} />
                <YAxis tick={{ fontSize: 9 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar
                  dataKey="booked_tonnes"
                  name="Booked tonnes"
                  stackId="a"
                  fill="#529273"
                />
                <Bar
                  dataKey="unserved_tonnes"
                  name="Unserved tonnes"
                  stackId="a"
                  fill="#e9d7b5"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="metric-summary">
            <span>
              Utilization {metrics.utilization_before_pct}% →{" "}
              {metrics.utilization_after_pct}%
            </span>
            <span>{metrics.backhaul_matches} booked backhaul matches</span>
            <span>{metrics.failed_match_count} unique failed matches</span>
          </div>
        </Panel>
      </div>
      <Panel title="Terminal activation & capacity gaps">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Terminal</th>
                <th>Nearby demand</th>
                <th>Reserved slots</th>
                <th>Storage demand gap</th>
                <th>Opportunity score</th>
              </tr>
            </thead>
            <tbody>
              {metrics.terminals.map((t: Data) => (
                <tr key={t.node_id}>
                  <td>{t.terminal}</td>
                  <td>{t.nearby_demand_tonnes} t</td>
                  <td>{t.reserved_slots}</td>
                  <td>{t.capacity_gap_tonnes} t</td>
                  <td>{t.activation_score}/100</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="provenance-mini">
          Platform demand, capabilities and access feed a transparent
          decision-support heuristic. Not an authoritative investment
          recommendation.
        </p>
      </Panel>
      {modal && (
        <Panel title="Modal-shift opportunity review">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Cargo</th>
                  <th>Route</th>
                  <th>Tonnage</th>
                  <th>Suitability</th>
                  <th>Suggested mode</th>
                </tr>
              </thead>
              <tbody>
                {modal.rows.map((r: Data, i: number) => (
                  <tr key={i}>
                    <td>{r.cargo_type}</td>
                    <td>
                      {r.origin} → {r.destination}
                    </td>
                    <td>{r.weight_tonnes} t</td>
                    <td>
                      <Badge value={r.suitability} />
                    </td>
                    <td>{r.recommended_mode || "No feasible plan"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
      <Panel title="Network evidence">
        <div className="detail-grid">
          <label>
            Selected bookings<strong>{metrics.selected_bookings}</strong>
          </label>
          <label>
            Completed bookings<strong>{metrics.completed_bookings}</strong>
          </label>
          <label>
            Unserved demand<strong>{metrics.unserved_tonnes} t</strong>
          </label>
          <label>
            Reliability observation sample
            <strong>
              {metrics.corridor_reliability.sample_count} completed plans
            </strong>
          </label>
          <label>
            Median estimated voyage
            <strong>
              {metrics.corridor_reliability.median_estimated_journey_hours ??
                "Insufficient data"}
            </strong>
          </label>
          <label>
            Factors source<strong>Prototype assumptions</strong>
          </label>
        </div>
        <p className="provenance-mini">{metrics.source}</p>
      </Panel>
    </>
  );
}
