import { useEffect, useState } from "react";
import {
  ArrowRight,
  Package,
  CalendarDays,
  Clock3,
  ShieldCheck,
  Truck,
  Ship,
  Layers,
  Leaf,
  Check,
  RefreshCw,
  Route,
} from "lucide-react";
import {
  api,
  money,
  date,
  title,
  type Cargo,
  type Data,
  type Act,
} from "../api";
import { Panel, Stat, Badge, Empty, Loading, Progress, CheckItem } from "./UI";
import RouteMap from "./RouteMap";
import { RateBenchmark } from "./NetworkIntelligence";

export default function Planner({
  data,
  role,
  act,
  busy,
  onBooked,
}: {
  data: Data;
  role: string;
  act: Act;
  busy: boolean;
  onBooked: () => void;
}) {
  const [cargoId, setCargoId] = useState("hero-cargo"),
    [vesselId, setVesselId] = useState("vembanad");
  const [matches, setMatches] = useState<Data | null>(null),
    [comparison, setComparison] = useState<Data | null>(null),
    [pool, setPool] = useState<Data | null>(null),
    [backhaul, setBackhaul] = useState<Data | null>(null),
    [broker, setBroker] = useState<Data | null>(null),
    [error, setError] = useState("");
  const cargo: Cargo | undefined =
    data.cargo.find((c: Cargo) => c.id === cargoId) || data.cargo[0];
  useEffect(() => {
    let active = true;
    if (!cargo) return;
    setComparison(null);
    Promise.all([
      api(`/cargo/${cargo.id}/matches`, role),
      api(`/cargo/${cargo.id}/compare?vessel_id=${vesselId}`, role),
    ])
      .then(([m, c]) => {
        if (active) {
          setMatches(m);
          setComparison(c);
          setError("");
        }
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [cargo?.id, role, vesselId]);
  async function book(mode: string) {
    if (!cargo) return;
    let success = false;
    await act(async () => {
      await api("/bookings", role, {
        cargo_id: cargo.id,
        vessel_id: vesselId,
        mode,
        pool_id: mode === "ROAD" ? null : pool?.pool?.id || null,
        approved: true,
      });
      success = true;
    }, "Booking confirmed. Your shipment is ready for dispatch.");
    if (success) onBooked();
  }
  const selectedVessel = data.vessels.find((v: Data) => v.id === vesselId);
  const percent =
    cargo && selectedVessel
      ? (cargo.weight_tonnes / selectedVessel.max_capacity_tonnes) * 100
      : 0;
  return (
    <>
      {error && (
        <div className="alert error" role="alert">
          {error}
        </div>
      )}
      <div className="stats-row">
        <Stat
          label="Active cargo requests"
          value={
            data.cargo.filter(
              (c: Cargo) => !["DELIVERED", "CANCELLED"].includes(c.status),
            ).length
          }
          note="Your freight demand"
        />
        <Stat
          label="Feasible vessel options"
          value={matches?.recommendations?.length ?? "—"}
          note="Route & terminal validated"
        />
        <Stat
          label="Potential vessel utilization"
          value={`${pool?.utilization_after_pct ?? percent.toFixed(1)}%`}
          note={
            pool
              ? "Calculated pool · pending booking"
              : "Selected cargo / vessel capacity"
          }
        />
        <Stat
          label="Estimated carbon reduction"
          value={
            comparison?.plans[2]?.feasible && comparison.plans[0]?.emissions_kg
              ? `${Math.round((1 - comparison.plans[2].emissions_kg / comparison.plans[0].emissions_kg) * 100)}%`
              : "—"
          }
          note="Against this cargo’s road baseline"
        />
      </div>
      {cargo && (
        <RateBenchmark cargoId={cargo.id} vesselId={vesselId} role={role} />
      )}
      <div className="planner-grid">
        <Panel
          title="Your next shipment"
          eyebrow="TRANSPORT DECISION"
          action={<Badge value={cargo?.status || "DRAFT"} />}
          className="cargo-panel"
        >
          {cargo ? (
            <>
              <label className="field cargo-selector">
                Cargo request
                <select
                  aria-label="Cargo request"
                  value={cargo.id}
                  onChange={(e) => {
                    setCargoId(e.target.value);
                    setPool(null);
                    setBackhaul(null);
                  }}
                >
                  {data.cargo.map((c: Cargo) => (
                    <option key={c.id} value={c.id}>
                      {title(c.cargo_type)} · {c.weight_tonnes} t · {c.origin}
                    </option>
                  ))}
                </select>
              </label>
              <div className="cargo-detail">
                <span className="cargo-icon">
                  <Package size={25} />
                </span>
                <div>
                  <h3>
                    {title(cargo.cargo_type)}
                    <span>{cargo.weight_tonnes} tonnes</span>
                  </h3>
                  <p>
                    {title(cargo.packaging)} ·{" "}
                    {cargo.volume_m3 ?? "Unverified volume"} m³ ·{" "}
                    {cargo.consolidation_allowed
                      ? "Pooling allowed"
                      : "Dedicated load"}
                  </p>
                </div>
              </div>
              <div className="origin-destination">
                <div>
                  <i />
                  <small>PICKUP</small>
                  <strong>{cargo.origin}</strong>
                </div>
                <div className="route-rule" />
                <div>
                  <i />
                  <small>DELIVERY</small>
                  <strong>{cargo.destination}</strong>
                </div>
              </div>
              <div className="shipment-meta">
                <div>
                  <CalendarDays size={16} />
                  <span>
                    Ready<strong>{date(cargo.ready_time)}</strong>
                  </span>
                </div>
                <div>
                  <Clock3 size={16} />
                  <span>
                    Deliver by<strong>{date(cargo.delivery_deadline)}</strong>
                  </span>
                </div>
              </div>
              <div className="validation-note">
                <ShieldCheck size={18} />
                <span>
                  Physical feasibility comes first.
                  <small>
                    Every option is checked against vessel, route and terminal
                    constraints.
                  </small>
                </span>
              </div>
            </>
          ) : (
            <Empty>Create a cargo request to compare transport options.</Empty>
          )}
        </Panel>
        <Panel
          title="A route with more possibility"
          eyebrow="WATERWAY INTELLIGENCE"
          className="map-panel"
          action={<span className="subtle">NW-3 · Kerala</span>}
        >
          <RouteMap data={data} />
          <div className="map-footer">
            <span>
              <i className="green-dot" />4 corridor terminals
            </span>
            <span>
              <Route size={15} />
              {comparison?.plans[2]?.water_km ?? "—"} km demo route
            </span>
            <span>
              <ShieldCheck size={15} />
              Feasibility checked
            </span>
          </div>
        </Panel>
      </div>
      <div className="section-heading">
        <div>
          <h2>Choose how your cargo moves</h2>
          <p>Complete delivered cost, arrival time and estimated emissions.</p>
        </div>
        <span className="subtle">
          <Leaf size={14} />
          Transparent prototype estimates
        </span>
      </div>
      <div className="mode-grid">
        {comparison ? (
          comparison.plans.map((p: Data) => {
            const Icon =
              p.mode === "ROAD" ? Truck : p.mode === "WATER" ? Ship : Layers;
            const recommended = p.mode === comparison.recommended_mode;
            return (
              <section
                key={p.mode}
                className={`mode-card ${recommended ? "recommended" : ""}`}
              >
                <div className="mode-head">
                  <span className="mode-icon">
                    <Icon size={23} />
                  </span>
                  <div>
                    <h3>{title(p.mode)}</h3>
                    <small>
                      {p.mode === "ROAD"
                        ? "Direct road freight"
                        : p.mode === "WATER"
                          ? "Terminal to terminal"
                          : "Road + water, connected"}
                    </small>
                  </div>
                  {recommended && (
                    <span className="recommended-tag">
                      <Check size={12} />
                      Recommended
                    </span>
                  )}
                </div>
                <div className="mode-cost">
                  {money(p.total_cost)}
                  <small>Total delivered cost</small>
                </div>
                {p.total_cost != null ? (
                  <>
                    <div className="mode-measures">
                      <div>
                        <Clock3 size={15} />
                        <span>
                          {p.hours} hrs<small>Transit & handling</small>
                        </span>
                      </div>
                      <div>
                        <Leaf size={15} />
                        <span>
                          {Math.round(p.emissions_kg)} kg
                          <small>Estimated CO₂</small>
                        </span>
                      </div>
                    </div>
                    <div className="mode-eta">
                      Arrival <strong>{date(p.eta)}</strong>
                      <Badge value={p.feasible ? "SLA_PASS" : "SLA_FAIL"} />
                    </div>
                    <details className="cost-details">
                      <summary>View charge breakdown</summary>
                      {Object.entries(p.breakdown).map(([k, v]) => (
                        <div key={k}>
                          <span>{title(k)}</span>
                          <span>{money(v as number)}</span>
                        </div>
                      ))}
                    </details>
                  </>
                ) : (
                  <div className="mode-unavailable">{p.reasons.join(" ")}</div>
                )}
                <button
                  className={`button ${recommended ? "primary" : ""} full`}
                  disabled={
                    busy ||
                    !p.feasible ||
                    [
                      "CONFIRMED",
                      "SCHEDULED",
                      "LOADING",
                      "IN_TRANSIT",
                      "UNLOADING",
                      "LAST_MILE",
                      "DELIVERED",
                    ].includes(cargo?.status || "")
                  }
                  onClick={() => book(p.mode)}
                >
                  {p.feasible
                    ? `Confirm ${pool && p.mode !== "ROAD" ? "pooled " : ""}${title(p.mode).toLowerCase()} booking`
                    : "Unavailable for this cargo"}
                  <ArrowRight size={15} />
                </button>
              </section>
            );
          })
        ) : (
          <Loading />
        )}
      </div>
      {comparison && (
        <div className="recommendation-note">
          <span className="ai-token">J</span>
          <div>
            <strong>Broker recommendation</strong>
            <p>
              {comparison.explanation} {comparison.source}
            </p>
          </div>
        </div>
      )}
      <Panel
        title="Agentic broker tools"
        eyebrow="UNDERSTAND → DECIDE → REVIEW"
        action={
          <button
            className="button small"
            disabled={busy || !cargo}
            onClick={() =>
              act(
                async () =>
                  setBroker(
                    await api("/broker", role, {
                      cargo_id: cargo!.id,
                      text: "Rank feasible vessels, compare delivered modes, pool compatible cargo and find a return load.",
                    }),
                  ),
                "Broker tool run completed.",
              )
            }
          >
            Run broker tools
          </button>
        }
      >
        {broker ? (
          <>
            <div className="metric-summary">
              {broker.trace.map((step: Data, i: number) => (
                <span key={i}>
                  <Badge value={step.status.toUpperCase()} />
                  {title(step.tool)}
                </span>
              ))}
            </div>
            <p className="provenance-mini">
              {broker.mode === "llm_tool_orchestration"
                ? "Configured LLM selected bounded tools."
                : "Deterministic local broker sequence; no LLM configured."}{" "}
              Safety, costs and optimization come from the validated tools.
              Booking requires your approval.
            </p>
          </>
        ) : (
          <p className="role-intro">
            A broker connects the planning tools and exposes their execution.
            Optional LLM tool selection uses the same constraint and
            optimization services.
          </p>
        )}
      </Panel>
      <div className="two-columns">
        <Panel
          title="Vessels that fit your freight"
          eyebrow="MATCHING & FEASIBILITY"
          action={
            <select
              aria-label="Select vessel"
              value={vesselId}
              onChange={(e) => {
                setVesselId(e.target.value);
                setPool(null);
              }}
            >
              {data.vessels.map((v: Data) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          }
        >
          {matches ? (
            <>
              <div className="match-list">
                {matches.recommendations.map((m: Data) => (
                  <div
                    className={`match-row ${m.vessel_id === vesselId ? "selected" : ""}`}
                    key={m.vessel_id}
                  >
                    <Ship size={22} />
                    <div>
                      <strong>{m.vessel_name}</strong>
                      <small>
                        {m.capacity_tonnes} t capacity ·{" "}
                        {Math.round(m.reliability * 100)}% reliability
                      </small>
                      <details>
                        <summary>Why this vessel?</summary>
                        {m.reasons.map((r: string) => (
                          <CheckItem passed key={r}>
                            {r}
                          </CheckItem>
                        ))}
                        <small>
                          Configurable score weights:{" "}
                          {JSON.stringify(m.weights)}
                        </small>
                      </details>
                    </div>
                    <span className="match-score">
                      {m.score}
                      <small>match score</small>
                    </span>
                    <button
                      className="text-button"
                      onClick={() => {
                        setVesselId(m.vessel_id);
                        setPool(null);
                      }}
                    >
                      Select
                    </button>
                  </div>
                ))}
              </div>
              {matches.rejected.map((m: Data) => (
                <details className="rejected-match" key={m.vessel_id}>
                  <summary>
                    <ShieldCheck size={16} />
                    <strong>{m.vessel_name}</strong>
                    <span>Commercial fit {m.commercial_score}%</span>
                    <Badge value="FAIL" />
                  </summary>
                  {m.feasibility.reasons.map((r: string) => (
                    <CheckItem passed={false} key={r}>
                      {r}
                    </CheckItem>
                  ))}
                </details>
              ))}
            </>
          ) : (
            <Loading />
          )}
        </Panel>
        <Panel title="Get more from this voyage" eyebrow="NETWORK OPTIMIZATION">
          <div className="opportunity">
            <span className="opportunity-icon">
              <Layers size={21} />
            </span>
            <div>
              <h3>Pool compatible cargo</h3>
              <p>Respect capacity, deadlines and co-load rules.</p>
            </div>
            <button
              className="button small"
              disabled={busy || !cargo}
              onClick={() =>
                act(
                  async () =>
                    setPool(
                      await api(
                        `/cargo/${cargo!.id}/pool?vessel_id=${vesselId}`,
                        role,
                        {},
                      ),
                    ),
                  "Compatible load pool calculated.",
                )
              }
            >
              Optimize
            </button>
          </div>
          {pool && (
            <div className="pool-result">
              <div>
                <strong>{pool.total_tonnes} t</strong>
                <span>
                  {pool.utilization_before_pct}% → {pool.utilization_after_pct}%
                  utilization
                </span>
              </div>
              <Progress value={pool.utilization_after_pct / 100} />
              <small>
                {pool.solver} · {pool.solver_status} · Preview until booking
                approval
              </small>
            </div>
          )}
          <div className="opportunity">
            <span className="opportunity-icon">
              <RefreshCw size={21} />
            </span>
            <div>
              <h3>Make the return count</h3>
              <p>Find a compatible load for the journey back.</p>
            </div>
            <button
              className="button small"
              disabled={busy || !cargo}
              onClick={() =>
                act(
                  async () =>
                    setBackhaul(
                      await api(
                        `/cargo/${cargo!.id}/backhaul?vessel_id=${vesselId}`,
                        role,
                        {},
                      ),
                    ),
                  "Return-load search completed.",
                )
              }
            >
              Find return
            </button>
          </div>
          {backhaul &&
            (backhaul.opportunities.length ? (
              <div className="backhaul-result">
                <Badge value="RETURN_LOAD_FOUND" />
                <h3>
                  {backhaul.opportunities[0].cargo_type} ·{" "}
                  {backhaul.opportunities[0].weight_tonnes} t
                </h3>
                <p>
                  {backhaul.opportunities[0].origin} →{" "}
                  {backhaul.opportunities[0].destination}
                </p>
                <strong>
                  {money(backhaul.opportunities[0].revenue)} potential freight
                  revenue
                </strong>
              </div>
            ) : (
              <Empty>No return load fits the vessel window.</Empty>
            ))}
          <p className="provenance-mini">
            Deterministic constraints + OR-Tools. Suggestions do not reserve
            capacity.
          </p>
        </Panel>
      </div>
    </>
  );
}
