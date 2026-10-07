import { useState, useEffect, useCallback } from "react";
import { Anchor, Check, Truck, ArrowRight, RefreshCw } from "lucide-react";
import {
  api,
  money,
  date,
  title,
  type Data,
  type Cargo,
  type Act,
} from "../api";
import { Panel, Stat, Badge, Empty, Loading } from "./UI";

type Props = {
  data: Data;
  role: string;
  act: Act;
  busy: boolean;
  view?: string;
  initialCargoId?: string;
  initialVesselId?: string;
  initialAvailabilityId?: string;
  newCargo?: () => void;
  replan?: (cargoId: string) => void;
  setView?: (view: string) => void;
  switchRole?: (role: string, vesselId?: string) => void;
};

export default function CargoLines({
  data,
  role,
  act,
  busy,
  view,
  initialCargoId,
  initialVesselId,
  initialAvailabilityId,
  newCargo,
  replan,
  setView,
  switchRole,
}: Props) {
  const [snapshot, setSnapshot] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [step, setStep] = useState(initialCargoId ? 2 : 1);
  const [selectedCargo, setSelectedCargo] = useState(initialCargoId || "");
  const [initialized, setInitialized] = useState(false);
  const [showAllCargo, setShowAllCargo] = useState(false);
  const [canSchedule, setCanSchedule] = useState(false);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [step]);
  const refresh = useCallback(async () => {
    try {
      setSnapshot(await api("/lines", role));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [role]);
  useEffect(() => {
    void refresh();
  }, [refresh, data]);
  useEffect(() => {
    if (initialCargoId) {
      setSelectedCargo(initialCargoId);
      setStep(2);
    }
  }, [initialCargoId]);
  useEffect(() => {
    if (role === "control" && view === "planner") setStep(2);
  }, [role, view]);
  useEffect(() => {
    if (snapshot && !initialized) {
      if (
        snapshot.departures.length &&
        (!initialCargoId ||
          snapshot.departures.some(
            (v: Data) =>
              ["HELD", "CONFIRMED", "COMPLETED"].includes(v.status) &&
              v.members.some((m: Data) => m.cargo_id === initialCargoId),
          ))
      )
        setStep(4);
      setInitialized(true);
    }
  }, [snapshot, initialized, initialCargoId]);
  const run: Act = (task, message) =>
    act(async () => {
      try {
        await task();
      } finally {
        await refresh();
      }
    }, message);
  if (!snapshot)
    return error ? <div className="alert error">{error}</div> : <Loading />;
  const pendingCargo = data.cargo
    .filter((c: Cargo) => ["POSTED", "MATCHED", "QUOTED"].includes(c.status))
    .sort(
      (a: Cargo, b: Cargo) =>
        Number(b.id === "hero-cargo") - Number(a.id === "hero-cargo"),
    );
  return (
    <div className="cargo-lines">
      {role === "shipper" && view !== "tracking" && (
        <>
          <nav className="journey-steps" aria-label="Delivery steps">
            {[
              "Choose cargo",
              "Compare boats & costs",
              "Plan departure",
              "Approve & track",
            ].map((label, index) => (
              <button
                key={label}
                aria-current={step === index + 1 ? "step" : undefined}
                className={step === index + 1 ? "current" : ""}
                disabled={index === 2 && !canSchedule}
                onClick={() => setStep(index + 1)}
              >
                <span>{index + 1}</span>
                <div>
                  {label}
                  <small>
                    {
                      [
                        "Cargo posting",
                        "Matching · Cost comparison",
                        "Schedule planning",
                        "One delivery booking",
                      ][index]
                    }
                  </small>
                </div>
              </button>
            ))}
          </nav>
          <div className="step-guidance" aria-live="polite">
            <span>STEP {step} OF 4</span>
            <strong>
              {
                [
                  "Start with what you need to send.",
                  "Find the right boat at the right price.",
                  "Choose when your cargo travels.",
                  "Approve the price. Follow your delivery.",
                ][step - 1]
              }
            </strong>
            <p>
              {
                [
                  "Post your own cargo, or try the sample below to explore the full journey.",
                  "Compare delivery costs to see road and water prices, arrival times and recommended boats.",
                  "Review departure and arrival dates. Sharing a boat with compatible cargo can reduce the cost.",
                  "Review each quote below. The boat operator and logistics coordinator then confirm the delivery.",
                ][step - 1]
              }
            </p>
          </div>
          {step === 1 && (
            <Panel
              title="1. Which cargo do you want to move?"
              eyebrow="CARGO POSTING"
              action={
                <button className="button primary" onClick={newCargo}>
                  Post new cargo
                </button>
              }
            >
              <p className="muted">
                Choose a request below to compare delivery options. The sample
                cement request is ready for the demonstration.
              </p>
              <div className="cargo-choice-grid">
                {(showAllCargo ? pendingCargo : pendingCargo.slice(0, 1)).map(
                  (c: Cargo) => (
                    <article className="cargo-choice" key={c.id}>
                      <div className="departure-head">
                        <Badge value={c.status} />
                        {data.demo_mode && c.id === "hero-cargo" && (
                          <span className="sample-tag">
                            Start here · sample
                          </span>
                        )}
                      </div>
                      <h3>
                        {title(c.cargo_type)} · {c.weight_tonnes} t
                      </h3>
                      <p>
                        {c.origin} → {c.destination}
                      </p>
                      <small>
                        Ready {date(c.ready_time)}
                        <br />
                        Deliver by {date(c.delivery_deadline)}
                      </small>
                      <button
                        className="button primary"
                        onClick={() => {
                          setSelectedCargo(c.id);
                          setStep(2);
                        }}
                      >
                        Compare this cargo <ArrowRight size={16} />
                      </button>
                    </article>
                  ),
                )}
              </div>
              {pendingCargo.length > 1 && (
                <button
                  className="button cargo-more"
                  aria-expanded={showAllCargo}
                  onClick={() => setShowAllCargo(!showAllCargo)}
                >
                  {showAllCargo
                    ? "Show fewer requests"
                    : `View ${pendingCargo.length - 1} more cargo requests`}
                </button>
              )}
              {!pendingCargo.length && (
                <Empty>Post a cargo request to start.</Empty>
              )}
            </Panel>
          )}
        </>
      )}
      {role === "operator" && view !== "tracking" && (
        <OperatorAvailability data={data} role={role} setView={setView} />
      )}
      {role === "control" && view === "overview" && (
        <div className="journey-intro">
          <Truck size={26} />
          <div>
            <h2>Your next task: confirm the delivery team.</h2>
            <p>
              Review the owner and boat approvals, then record each truck and
              terminal response. Confirm the bundle when every check is
              complete.
            </p>
            <button className="button" onClick={() => setView?.("planner")}>
              Plan a new departure <ArrowRight size={15} />
            </button>
          </div>
        </div>
      )}
      {((role === "shipper" && view !== "tracking") ||
        (role === "control" && view === "planner")) && (
        <div hidden={role === "shipper" && ![2, 3].includes(step)}>
          <CargoAdvice
            data={data}
            role={role}
            act={run}
            busy={busy}
            stage={role === "control" && step < 2 ? 2 : step}
            selectedCargoId={selectedCargo}
            initialVesselId={initialVesselId}
            initialAvailabilityId={initialAvailabilityId}
            onStage={setStep}
            onCanSchedule={setCanSchedule}
            onProposed={() => {
              setStep(4);
              setCanSchedule(false);
              if (role === "control") setView?.("overview");
            }}
          />
        </div>
      )}
      {role === "control" && view === "tracking" && snapshot.impact && (
        <>
          <div className="stats-row">
            <Stat
              label="Selected water tonnes"
              value={`${snapshot.impact.selected_water_tonnes} t`}
              note="Active commitments plus completed deliveries"
            />
            <Stat
              label="Completed water tonnes"
              value={`${snapshot.impact.completed_water_tonnes} t`}
              note="Recorded door-receipt quantities"
            />
            <Stat
              label="Estimated CO₂ avoided"
              value={`${snapshot.impact.estimated_full_delivery_co2_avoided_kg} kg`}
              note="Full delivery tonne-km estimate · synthetic factors"
            />
          </div>
          <p className="muted">
            {snapshot.impact.long_haul_truck_equivalents} long-haul truck
            equivalents; {snapshot.impact.connecting_truck_trips} connecting
            trips. Estimates do not establish a net reduction in trucks.
          </p>
        </>
      )}
      {(role !== "shipper" || step === 4 || view === "tracking") &&
        view !== "planner" && (
          <Panel
            title={
              role === "operator"
                ? "Your dated departures"
                : role === "control"
                  ? "Departures needing coordination"
                  : "4. Approve your quotes and track delivery"
            }
          >
            {!snapshot.departures.length && (
              <Empty>
                {role === "shipper"
                  ? "No delivery plan yet. Start by choosing cargo, then compare costs and request a departure."
                  : role === "operator"
                    ? "No departure requests yet. List your availability so cargo owners can find your boat."
                    : "No departure requests yet. Plan a departure for entrusted cargo, or let an owner request one."}
                {role === "shipper" && (
                  <button
                    className="button primary"
                    onClick={() => {
                      setStep(1);
                      setView?.("overview");
                    }}
                  >
                    Choose cargo
                  </button>
                )}
              </Empty>
            )}
            {snapshot.departures
              .filter(
                (v: Data) =>
                  role !== "shipper" ||
                  view === "tracking" ||
                  !selectedCargo ||
                  v.members.some((m: Data) => m.cargo_id === selectedCargo),
              )
              .map((voyage: Data) => (
                <Departure
                  key={voyage.id}
                  voyage={voyage}
                  role={role}
                  act={run}
                  busy={busy}
                  switchRole={switchRole}
                  replan={replan}
                />
              ))}
          </Panel>
        )}
      <div className="line-source">
        <Anchor size={17} />
        <span>
          Local prototype · Synthetic rates and CO₂ factors · Provider responses
          are simulated
        </span>
        <button
          className="icon-button"
          aria-label="Refresh departures"
          onClick={refresh}
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </div>
  );
}

function CargoAdvice({
  data,
  role,
  act,
  busy,
  stage,
  onStage,
  selectedCargoId,
  initialVesselId,
  initialAvailabilityId,
  onProposed,
  onCanSchedule,
}: Props & {
  stage: number;
  onStage: (stage: number) => void;
  selectedCargoId: string;
  onProposed: () => void;
  onCanSchedule: (ready: boolean) => void;
}) {
  const available = data.cargo.filter((c: Cargo) =>
    ["POSTED", "MATCHED", "QUOTED"].includes(c.status),
  );
  const [cargoId, setCargoId] = useState(
    () =>
      available.find((c: Cargo) => c.id === "hero-cargo")?.id ||
      available[0]?.id ||
      "",
  );
  const [vesselId, setVesselId] = useState(
    initialVesselId || data.vessels[0]?.id || "",
  );
  const [availabilityId, setAvailabilityId] = useState(
    initialAvailabilityId || "",
  );
  const [advice, setAdvice] = useState<Data | null>(null),
    [matches, setMatches] = useState<Data | null>(null);
  const [profile, setProfile] = useState<Data | null>(null),
    [profileReady, setProfileReady] = useState(false);
  const [selected, setSelected] = useState<string[]>([]),
    [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [notBefore, setNotBefore] = useState("");
  const [scheduleDirty, setScheduleDirty] = useState(false);
  useEffect(() => {
    onCanSchedule(Boolean(advice?.water && profileReady && !loading));
  }, [advice, profileReady, loading, onCanSchedule]);
  useEffect(() => {
    if (selectedCargoId) setCargoId(selectedCargoId);
  }, [selectedCargoId]);
  useEffect(() => {
    if (!available.some((c: Cargo) => c.id === cargoId))
      setCargoId(available[0]?.id || "");
  }, [data, cargoId]);
  useEffect(() => {
    setAdvice(null);
    setNotBefore("");
    setScheduleDirty(false);
    setMatches(null);
    setSelected([]);
    setProfileReady(false);
    setProfile(null);
    setError("");
    if (!cargoId) return;
    let current = true;
    api(`/lines/cargo/${cargoId}/profile`, role)
      .then((result) => {
        if (!current) return;
        setProfileReady(Boolean(result.profile));
        setProfile(
          result.profile || {
            heaviest_piece_tonnes: "",
            pieces: "",
            unit_length_m: 1,
            unit_width_m: 1,
            unit_height_m: 1,
          },
        );
      })
      .catch((e) => {
        if (current) setError(e.message);
      });
    return () => {
      current = false;
    };
  }, [cargoId, role]);
  const cargo: Cargo | undefined = available.find(
    (c: Cargo) => c.id === cargoId,
  );
  async function compare(
    crossover = false,
    chosenVessel = vesselId,
    requestedDeparture = notBefore,
  ) {
    setLoading(true);
    setError("");
    try {
      const [costs, matched] = await Promise.all([
        api(
          `/lines/cargo/${cargoId}/advice?vessel_id=${chosenVessel}&crossover=${crossover}${availabilityId && chosenVessel === vesselId ? `&availability_id=${encodeURIComponent(availabilityId)}` : ""}${requestedDeparture ? `&not_before=${encodeURIComponent(new Date(requestedDeparture + ":00+05:30").toISOString())}` : ""}`,
          role,
        ),
        api(`/cargo/${cargoId}/matches`, role),
      ]);
      setAdvice(costs);
      setMatches(matched);
      setScheduleDirty(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  const [autoCompared, setAutoCompared] = useState("");
  useEffect(() => {
    const key = `${cargoId}-${vesselId}`;
    if (
      initialVesselId &&
      profileReady &&
      cargoId === selectedCargoId &&
      autoCompared !== key
    ) {
      setAutoCompared(key);
      void compare();
    }
  }, [
    initialVesselId,
    profileReady,
    cargoId,
    selectedCargoId,
    vesselId,
    autoCompared,
  ]);
  const candidates = available.filter(
    (c: Cargo) =>
      c.id !== cargoId &&
      c.destination === cargo?.destination &&
      new Date(c.ready_time) <= new Date(cargo.delivery_deadline) &&
      new Date(c.delivery_deadline) >= new Date(cargo.ready_time) &&
      c.consolidation_allowed &&
      cargo?.consolidation_allowed,
  );
  return (
    <Panel
      title={
        stage === 3
          ? "3. Plan your departure"
          : "2. Find a boat and compare the full cost"
      }
      eyebrow={
        stage === 3
          ? "SCHEDULE PLANNING"
          : "MATCHING RECOMMENDATIONS · COST COMPARISON"
      }
    >
      {!available.length ? (
        <Empty>Post a cargo request to start a delivery.</Empty>
      ) : (
        <>
          <p className="muted">
            {stage === 3
              ? "Add compatible loads to share sailing and terminal costs. Each owner approves a separate quote."
              : "Select your cargo and a boat. Compare the complete delivered price, arrival time and safety checks before continuing."}
          </p>
          <div hidden={stage === 3} className="line-form">
            <label>
              Cargo request
              <select
                aria-label="Cargo request"
                disabled={busy || loading}
                value={cargoId}
                onChange={(e) => setCargoId(e.target.value)}
              >
                {available.map((c: Cargo) => (
                  <option key={c.id} value={c.id}>
                    {title(c.cargo_type)} · {c.weight_tonnes} t · {c.origin} →{" "}
                    {c.destination}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Available boat
              <select
                aria-label="Listed vessel"
                disabled={busy || loading}
                value={vesselId}
                onChange={(e) => {
                  setVesselId(e.target.value);
                  setAvailabilityId("");
                  setAdvice(null);
                  setSelected([]);
                }}
              >
                {data.vessels.map((v: Data) => (
                  <option key={v.id} value={v.id}>
                    {v.name} · {v.max_capacity_tonnes} t
                  </option>
                ))}
              </select>
            </label>
            <button
              className="button primary"
              disabled={busy || loading || !cargoId || !profileReady}
              onClick={() => compare()}
            >
              {loading ? "Computing…" : "Compare delivery costs"}
            </button>
          </div>
          {cargo && (
            <p className="muted">
              Ready {date(cargo.ready_time)} · Deliver by{" "}
              {date(cargo.delivery_deadline)}
            </p>
          )}
          {!profileReady && profile && (
            <div className="load-review">
              <div className="quick-load-banner">
                <div>
                  <strong>Need a quick plan? Use standard dimensions</strong>
                  <p>
                    Apply 1m × 1m standard units with 1 click to unlock cost
                    comparison immediately.
                  </p>
                </div>
                <button
                  type="button"
                  className="button primary"
                  disabled={busy}
                  onClick={() => {
                    const w = cargo?.weight_tonnes || 1;
                    const pieces = Math.max(1, Math.round(w));
                    const heaviest = Math.min(
                      w,
                      Math.round((w / pieces) * 100) / 100,
                    );
                    const std = {
                      heaviest_piece_tonnes: heaviest,
                      pieces: pieces,
                      unit_length_m: 1,
                      unit_width_m: 1,
                      unit_height_m: 1,
                    };
                    setProfile(std);
                    void act(async () => {
                      await api(`/lines/cargo/${cargoId}/profile`, role, std);
                      setProfileReady(true);
                    }, "Standard load dimensions applied.");
                  }}
                >
                  Apply standard dimensions (1-click)
                </button>
              </div>
              <h3>Review load units before requesting a departure</h3>
              <p className="muted">
                Truck and lift checks need your heaviest piece, piece count and
                largest unit dimensions.
              </p>
              <div className="line-form">
                {[
                  ["heaviest_piece_tonnes", "Heaviest piece (t)"],
                  ["pieces", "Number of pieces"],
                  ["unit_length_m", "Largest unit length (m)"],
                  ["unit_width_m", "Largest unit width (m)"],
                  ["unit_height_m", "Largest unit height (m)"],
                ].map(([key, label]) => (
                  <label key={key}>
                    {label}
                    <input
                      aria-label={label}
                      type="number"
                      min="0.001"
                      step={key === "pieces" ? "1" : ".001"}
                      value={profile[key]}
                      onChange={(e) =>
                        setProfile({ ...profile, [key]: e.target.value })
                      }
                    />
                  </label>
                ))}
              </div>
              <button
                className="button"
                disabled={
                  busy || !profile.heaviest_piece_tonnes || !profile.pieces
                }
                onClick={() =>
                  act(async () => {
                    await api(
                      `/lines/cargo/${cargoId}/profile`,
                      role,
                      Object.fromEntries(
                        Object.entries(profile).map(([k, v]) => [k, Number(v)]),
                      ),
                    );
                    setProfileReady(true);
                  }, "Load units reviewed.")
                }
              >
                Save reviewed load units
              </button>
            </div>
          )}
          {error && (
            <div role="alert" className="alert error">
              {error}
            </div>
          )}
          {advice && (
            <>
              <div hidden={stage === 3}>
                <div className="line-cost-grid">
                  <CostCard
                    heading="All-road delivery"
                    plan={advice.road}
                    recommended={advice.recommended_mode === "ROAD"}
                  />
                  <CostCard
                    heading="Water + connecting trucks"
                    plan={advice.water}
                    reasons={advice.water_rejection_reasons}
                    recommended={
                      advice.recommended_mode !== "ROAD" &&
                      Boolean(advice.water)
                    }
                  />
                </div>
                <details className="line-note">
                  <summary>Cost assumptions and crossover analysis</summary>
                  <p className="muted">
                    {advice.source}. Truck tariff is the greater of the trip
                    minimum and distance charge. Quote includes sailing and
                    terminal setup charges.
                  </p>
                  <button
                    className="button small"
                    disabled={loading || !profileReady}
                    onClick={() => compare(true)}
                  >
                    Find feasible crossover ranges
                  </button>
                  {advice.crossover_ranges_tonnes && (
                    <div className="line-note">
                      {advice.crossover_ranges_tonnes.length
                        ? `Water costs less at sampled loads: ${advice.crossover_ranges_tonnes.map((r: number[]) => `${r[0]}–${r[1]} t`).join(", ")}.`
                        : "No feasible water-cost crossover found in the sampled range."}
                      <small>{advice.crossover_basis}</small>
                    </div>
                  )}
                </details>
                {matches && (
                  <div className="matching-results">
                    <h3>Matching recommendations</h3>
                    <p className="muted">
                      Ranked boats that pass the cargo and route checks. The
                      chosen departure also checks truck, lift and
                      shared-resource availability.
                    </p>
                    <div className="boat-match-grid">
                      {matches.recommendations.map((m: Data, index: number) => {
                        const vessel = data.vessels.find(
                          (v: Data) => v.id === m.vessel_id,
                        );
                        const listing = data.availability.find(
                          (a: Data) => a.vessel_id === m.vessel_id,
                        );
                        return (
                          <article
                            className={`boat-match ${m.vessel_id === vesselId ? "selected" : ""}`}
                            key={m.vessel_id}
                          >
                            <span className="muted">
                              Recommendation {index + 1}
                            </span>
                            <h4>{vessel?.name || m.vessel_id}</h4>
                            <p>
                              {vessel?.max_capacity_tonnes} t capacity ·{" "}
                              {vessel?.max_volume_m3} m³
                            </p>
                            <small>
                              Listed {date(listing?.available_from)} to{" "}
                              {date(listing?.available_until)}
                            </small>
                            <Badge value="FEASIBILITY_PASS" />
                            <button
                              className="button small"
                              disabled={busy || loading}
                              onClick={() => {
                                setVesselId(m.vessel_id);
                                setAvailabilityId("");
                                setSelected([]);
                                void compare(false, m.vessel_id);
                              }}
                            >
                              {m.vessel_id === vesselId
                                ? "Selected boat"
                                : "Compare this boat"}
                            </button>
                          </article>
                        );
                      })}
                    </div>
                    {!!matches.rejected.length && (
                      <div className="rejected-boats">
                        <h4>Boats excluded by safety checks</h4>
                        {matches.rejected.map((m: Data) => (
                          <p key={m.vessel_id}>
                            <strong>
                              {data.vessels.find(
                                (v: Data) => v.id === m.vessel_id,
                              )?.name || m.vessel_id}
                            </strong>{" "}
                            · {m.feasibility.reasons.join(" ")}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {advice.water && profileReady && (
                  <button className="button primary" onClick={() => onStage(3)}>
                    Continue to schedule planning <ArrowRight size={16} />
                  </button>
                )}
                {!advice.water && (
                  <p className="line-note">
                    Choose another recommended boat to continue with a water
                    delivery. The road quote remains available for comparison.
                  </p>
                )}
              </div>
              {stage === 3 && !advice.water && (
                <div className="schedule-unavailable" role="alert">
                  <h3>This departure is unavailable</h3>
                  <p>{advice.water_rejection_reasons.join(" ")}</p>
                  <button
                    className="button"
                    disabled={loading || busy}
                    onClick={() => {
                      setNotBefore("");
                      void compare(false, vesselId, "");
                    }}
                  >
                    Find earliest available departure
                  </button>
                  <button className="button" onClick={() => onStage(2)}>
                    Choose another boat
                  </button>
                </div>
              )}
              {stage === 3 && advice.water && profileReady && (
                <div className="pool-choice">
                  <div className="schedule-summary">
                    <h3>
                      {data.vessels.find((v: Data) => v.id === vesselId)?.name}
                    </h3>
                    <div>
                      <span>Water departure</span>
                      <strong>{date(advice.water.departure)}</strong>
                    </div>
                    <div>
                      <span>Your door arrival</span>
                      <strong>{date(advice.water.eta)}</strong>
                    </div>
                    <div>
                      <span>Your unpooled quote</span>
                      <strong>{money(advice.water.total_cost)}</strong>
                    </div>
                  </div>
                  <div className="preferred-departure">
                    <label>
                      Preferred departure (IST)
                      <input
                        aria-label="Preferred departure (IST)"
                        type="datetime-local"
                        value={notBefore}
                        onChange={(e) => {
                          setNotBefore(e.target.value);
                          setScheduleDirty(true);
                        }}
                      />
                      <small>
                        Optional. We’ll find a safe departure at or after this
                        time.
                      </small>
                    </label>
                    <button
                      className="button"
                      disabled={busy || loading}
                      onClick={() => compare()}
                    >
                      {loading ? "Checking dates…" : "Update departure"}
                    </button>
                  </div>
                  {scheduleDirty && (
                    <p className="line-note">
                      Update departure to check your chosen time before
                      requesting a booking.
                    </p>
                  )}
                  <h3>Add loads to share this departure</h3>
                  <p className="muted">
                    Select your other loads. Combined weight, volume, terminal
                    jobs and each delivery deadline are rechecked.
                  </p>
                  <button
                    className="button small"
                    disabled={busy}
                    onClick={() =>
                      act(async () => {
                        const result = await api(
                          `/cargo/${cargoId}/pool?vessel_id=${vesselId}`,
                          role,
                          {},
                        );
                        setSelected(
                          result.cargo
                            .map((c: Data) => c.id)
                            .filter((id: string) => id !== cargoId),
                        );
                      }, "OR-Tools suggested compatible loads. The departure rechecks shared jobs and economics.")
                    }
                  >
                    Suggest compatible loads
                  </button>
                  {candidates.map((c: Cargo) => (
                    <label className="line-check" key={c.id}>
                      <input
                        type="checkbox"
                        checked={selected.includes(c.id)}
                        onChange={(e) =>
                          setSelected(
                            e.target.checked
                              ? [...selected, c.id]
                              : selected.filter((id) => id !== c.id),
                          )
                        }
                      />
                      {title(c.cargo_type)} · {c.weight_tonnes} t · {c.origin} →{" "}
                      {c.destination}
                    </label>
                  ))}
                  <button
                    className="button primary"
                    disabled={busy || loading || scheduleDirty}
                    onClick={() =>
                      act(async () => {
                        await api("/lines/proposals", role, {
                          cargo_ids: [cargoId, ...selected],
                          vessel_id: vesselId,
                          ...(availabilityId
                            ? { availability_id: availabilityId }
                            : {}),
                          ...(notBefore
                            ? {
                                not_before: new Date(
                                  notBefore + ":00+05:30",
                                ).toISOString(),
                              }
                            : {}),
                        });
                        onProposed();
                      }, "Departure held for 20 minutes. Review and approve each exact quote.")
                    }
                  >
                    Request dated departure <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </Panel>
  );
}

function OperatorAvailability({
  data,
  role,
  setView,
}: Pick<Props, "data" | "role" | "setView">) {
  const [vesselId, setVesselId] = useState(data.vessels[0]?.id || "");
  const [opportunities, setOpportunities] = useState<Data | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true;
    setOpportunities(null);
    setError("");
    if (vesselId)
      api(`/vessels/${vesselId}/opportunities`, role)
        .then((result) => {
          if (current) setOpportunities(result);
        })
        .catch((e) => {
          if (current) setError(e.message);
        });
    return () => {
      current = false;
    };
  }, [vesselId, role, data]);
  return (
    <>
      <div className="journey-intro">
        <Anchor size={26} />
        <div>
          <h2>1. Make your boat available</h2>
          <p>
            Publish capacity and dates. Cargo owners can then find your boat and
            request a dated departure.
          </p>
          <div className="button-row">
            <button
              className="button primary"
              onClick={() => setView?.("voice")}
            >
              List boat availability <ArrowRight size={16} />
            </button>
            <button className="button" onClick={() => setView?.("fleet")}>
              Manage vessels
            </button>
          </div>
        </div>
      </div>
      <Panel title="Boat availability listing" eyebrow="YOUR OWN VESSELS">
        <div className="cargo-choice-grid">
          {data.vessels.map((v: Data) => (
            <article className="cargo-choice" key={v.id}>
              <h3>{v.name}</h3>
              <p>
                {v.max_capacity_tonnes} t · {v.max_volume_m3} m³
              </p>
              {data.availability
                .filter((a: Data) => a.vessel_id === v.id)
                .map((a: Data) => (
                  <div className="availability-window" key={a.id}>
                    <strong>
                      {a.origin} → {a.destination}
                    </strong>
                    <small>
                      {a.capacity_tonnes} t listed
                      <br />
                      {date(a.available_from)} to {date(a.available_until)}
                    </small>
                  </div>
                ))}
              {!data.availability.some((a: Data) => a.vessel_id === v.id) && (
                <p className="muted">No dates listed yet.</p>
              )}
            </article>
          ))}
        </div>
      </Panel>
      <Panel
        title="2. Review compatible cargo demand"
        eyebrow="MATCHING RECOMMENDATIONS"
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
        <p className="muted">
          Demand is a preview. A sailing request below has exact quotes, owner
          approvals and modeled contribution.
        </p>
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        {!opportunities && !error && <Loading />}
        <div className="demand-list">
          {opportunities?.cargo.map((c: Data) => (
            <div key={c.id}>
              <strong>
                {title(c.cargo_type)} · {c.weight_tonnes} t
              </strong>
              <span>
                {c.origin} → {c.destination}
              </span>
              <small>Estimated arrival {date(c.eta)}</small>
            </div>
          ))}
        </div>
        {opportunities && !opportunities.cargo.length && (
          <Empty>No unbooked compatible demand for this vessel.</Empty>
        )}
      </Panel>
    </>
  );
}

function CostCard({ heading, plan, reasons = [], recommended }: Data) {
  return (
    <div className={`line-cost ${recommended ? "recommended" : ""}`}>
      <h3>{heading}</h3>
      {!plan || !plan.feasible ? (
        <p>
          {[...reasons, ...(plan?.reasons || [])].join(" ") ||
            "No feasible quote."}
        </p>
      ) : (
        <>
          <strong className="line-price">{money(plan.total_cost)}</strong>
          {recommended && <Badge value="LOWEST_FEASIBLE_COST" />}
          <p>Arrives by {date(plan.eta)}</p>
          <p>
            {plan.truck_trips ?? plan.first_mile_trips + plan.last_mile_trips}{" "}
            truck trips · Estimated {plan.emissions_kg} kg CO₂
          </p>
          <details>
            <summary>Itemized delivery price</summary>
            {Object.entries(plan.breakdown as Record<string, number>).map(
              ([key, value]) => (
                <div className="line-charge" key={key}>
                  <span>{title(key)}</span>
                  <strong>{money(value)}</strong>
                </div>
              ),
            )}
          </details>
        </>
      )}
    </div>
  );
}

function Departure({
  voyage,
  role,
  act,
  busy,
  switchRole,
  replan,
}: {
  voyage: Data;
  role: string;
  act: Act;
  busy: boolean;
  switchRole?: (role: string, vesselId?: string) => void;
  replan?: (cargoId: string) => void;
}) {
  const [alternatives, setAlternatives] = useState<Data | null>(null);
  const allAccepted = voyage.members.every((m: Data) => m.accepted),
    held = voyage.status === "HELD";
  const confirmed = voyage.status === "CONFIRMED";
  const canConfirm =
    voyage.owners_ready && voyage.operator_accepted && voyage.providers_ready;
  const blocker = !voyage.owners_ready
    ? "Waiting for cargo owners to approve every quote."
    : !voyage.operator_accepted
      ? "Waiting for the boat operator to accept this departure."
      : !voyage.providers_ready
        ? "Waiting for the coordinator to record every truck and terminal response."
        : "All approvals complete. Ready to confirm the delivery bundle.";
  const activeMembers = voyage.members.filter(
    (m: Data) => !["CANCELLED", "DELIVERED"].includes(m.status),
  );
  const state = activeMembers[0]?.status;
  const next = (
    {
      CONFIRMED: "SCHEDULED",
      SCHEDULED: "LOADING",
      LOADING: "IN_TRANSIT",
      IN_TRANSIT: "UNLOADING",
    } as Record<string, string>
  )[state];
  return (
    <article className="departure" data-testid="departure">
      <div className="departure-head">
        <div>
          <small>Shared waterway departure</small>
          <h3>
            {voyage.vessel_name} · {date(voyage.departure)}
          </h3>
        </div>
        <Badge value={voyage.status} />
      </div>
      <div
        className="departure-progress-stepper"
        aria-label="Delivery progress"
      >
        <div className={`step-item ${voyage.owners_ready ? "done" : "active"}`}>
          <div className="step-circle">
            {voyage.owners_ready ? <Check size={14} /> : "1"}
          </div>
          <span>1. Owner Quotes</span>
        </div>
        <div className={`step-line ${voyage.owners_ready ? "done" : ""}`} />
        <div
          className={`step-item ${voyage.operator_accepted ? "done" : voyage.owners_ready ? "active" : ""}`}
        >
          <div className="step-circle">
            {voyage.operator_accepted ? <Check size={14} /> : "2"}
          </div>
          <span>2. Boat Operator</span>
        </div>
        <div
          className={`step-line ${voyage.operator_accepted ? "done" : ""}`}
        />
        <div
          className={`step-item ${voyage.providers_ready && confirmed ? "done" : voyage.operator_accepted ? "active" : ""}`}
        >
          <div className="step-circle">
            {voyage.providers_ready && confirmed ? <Check size={14} /> : "3"}
          </div>
          <span>3. Delivery Team</span>
        </div>
        <div className={`step-line ${confirmed ? "done" : ""}`} />
        <div
          className={`step-item ${state === "DELIVERED" ? "done" : confirmed ? "active" : ""}`}
        >
          <div className="step-circle">
            {state === "DELIVERED" ? <Check size={14} /> : "4"}
          </div>
          <span>
            {state === "DELIVERED" ? "4. Delivered" : "4. In Transit"}
          </span>
        </div>
      </div>
      {held && (
        <div className="booking-next-action-card">
          {!voyage.owners_ready ? (
            <div className="action-state">
              <div className="action-info">
                <strong>Next step: Approve delivery quote</strong>
                <p>
                  Acceptance unlocks after every cargo owner approves their
                  quote.
                </p>
              </div>
              {role === "shipper" ? (
                voyage.members.some((m: Data) => !m.accepted && m.quote) && (
                  <button
                    type="button"
                    className="button primary"
                    disabled={busy}
                    onClick={() =>
                      act(async () => {
                        const pendingQuotes = voyage.members.filter(
                          (m: Data) => !m.accepted && m.quote,
                        );
                        for (const m of pendingQuotes) {
                          await api(
                            `/lines/quotes/${m.quote.id}/approve`,
                            role,
                            {},
                          );
                        }
                      }, "All quotes approved. Boat operator can now accept.")
                    }
                  >
                    Approve all quotes now <ArrowRight size={15} />
                  </button>
                )
              ) : switchRole ? (
                <button
                  type="button"
                  className="button small"
                  onClick={() => switchRole("shipper")}
                >
                  Open cargo owner workspace <ArrowRight size={15} />
                </button>
              ) : null}
            </div>
          ) : !voyage.operator_accepted ? (
            <div className="action-state">
              <div className="action-info">
                <strong>Next step: Boat operator acceptance</strong>
                <p>
                  {role !== "shipper" &&
                  !voyage.accepted_economics?.covers_modeled_costs
                    ? "The operator must review the estimated shortfall before accepting this approved price."
                    : "Quotes approved. The boat operator can now review and accept this scheduled departure."}
                </p>
              </div>
              {role === "operator" ? (
                <button
                  type="button"
                  className="button primary"
                  disabled={
                    busy ||
                    !allAccepted ||
                    voyage.operator_accepted ||
                    !voyage.accepted_economics.covers_modeled_costs
                  }
                  onClick={() =>
                    act(
                      () =>
                        api(`/lines/${voyage.id}/operator-response`, role, {
                          version: voyage.version,
                          accept: true,
                        }),
                      "Operator accepted the reviewed departure.",
                    )
                  }
                >
                  Accept reviewed departure <ArrowRight size={15} />
                </button>
              ) : switchRole ? (
                <button
                  type="button"
                  className="button small"
                  onClick={() => switchRole("operator", voyage.vessel_id)}
                >
                  Open boat operator workspace <ArrowRight size={15} />
                </button>
              ) : null}
            </div>
          ) : !voyage.providers_ready ? (
            <div className="action-state">
              <div className="action-info">
                <strong>Next step: Coordinator arranging delivery team</strong>
                <p>
                  Boat accepted. Coordinator will record truck & terminal
                  responses.
                </p>
              </div>
              {switchRole && role !== "control" && (
                <button
                  type="button"
                  className="button small"
                  onClick={() => switchRole("control")}
                >
                  Open logistics coordinator workspace <ArrowRight size={15} />
                </button>
              )}
            </div>
          ) : (
            <div className="action-state">
              <div className="action-info">
                <strong>All approvals complete!</strong>
                <p>Ready to confirm delivery bundle.</p>
              </div>
            </div>
          )}
        </div>
      )}
      <div className="next-task">
        <span>WHAT HAPPENS NEXT</span>
        <strong>{held ? blocker : voyage.next_action}</strong>
        <small>{voyage.service_owner} coordinates this delivery.</small>
      </div>
      {role === "shipper" &&
        replan &&
        ["EXPIRED", "DECLINED"].includes(voyage.status) && (
          <div className="button-row">
            <p>
              This departure was not booked. Choose a boat to review a fresh
              price and schedule.
            </p>
            {voyage.members.map((member: Data) => (
              <button
                className="button primary"
                key={member.cargo_id}
                onClick={() => replan(member.cargo_id)}
              >
                Find a boat for {title(member.cargo_type)} ·{" "}
                {member.weight_tonnes} t <ArrowRight size={16} />
              </button>
            ))}
          </div>
        )}
      <p className="muted">
        {voyage.weight_tonnes} t · {(voyage.utilization * 100).toFixed(1)}%
        vessel utilization · Confirmation cutoff {date(voyage.cutoff)}
        {held && ` · Quote expires ${date(voyage.expires_at)}`}
      </p>
      {role !== "shipper" && voyage.projected_economics && (
        <div
          className={`contribution ${voyage.accepted_economics.covers_modeled_costs ? "positive" : "pending"}`}
        >
          <span>Modeled sailing contribution from accepted loads</span>
          <strong>
            {money(voyage.accepted_economics.contribution_minor / 100)}
          </strong>
          <p>
            {voyage.accepted_economics.covers_modeled_costs
              ? "Accepted delivery revenue covers modeled voyage costs."
              : "Accepted delivery revenue does not yet cover modeled voyage costs."}{" "}
            Revenue {money(voyage.accepted_economics.revenue_minor / 100)} ·
            Provider payables and operating allowance{" "}
            {money(voyage.accepted_economics.operating_cost_minor / 100)}.
          </p>
          <details>
            <summary>Proposed contribution and calculation basis</summary>
            <small>
              All proposed loads:{" "}
              {money(voyage.projected_economics.contribution_minor / 100)}{" "}
              contribution. {voyage.accepted_economics.basis}
            </small>
          </details>
          {voyage.viability_warning && (
            <p className="alert">
              Cancellation lowered contribution. Remaining customer prices and
              common reservations stay committed.
            </p>
          )}
        </div>
      )}
      <div className="line-acceptance">
        <Check size={16} /> Operator{" "}
        {voyage.operator_accepted
          ? `accepted version ${voyage.version}`
          : "acceptance pending"}{" "}
        · {voyage.accepted_job_count}/{voyage.job_count} provider jobs accepted
        · Simulation
      </div>
      {held && (
        <div
          className="approval-checklist"
          aria-label="Delivery approval checklist"
        >
          <div className={voyage.owners_ready ? "complete" : ""}>
            <Check size={16} />
            <span>
              Cargo owners
              <small>
                {voyage.members.filter((m: Data) => m.accepted).length}/
                {voyage.members.length} quotes approved
              </small>
            </span>
          </div>
          <div className={voyage.operator_accepted ? "complete" : ""}>
            <Check size={16} />
            <span>
              Boat operator
              <small>
                {voyage.operator_accepted
                  ? "Departure accepted"
                  : "Acceptance pending"}
              </small>
            </span>
          </div>
          <div className={voyage.providers_ready ? "complete" : ""}>
            <Check size={16} />
            <span>
              Delivery providers
              <small>
                {voyage.accepted_job_count}/{voyage.job_count} jobs accepted
              </small>
            </span>
          </div>
        </div>
      )}
      {role === "operator" && held && !allAccepted && (
        <p className="line-note">
          Acceptance unlocks after every cargo owner approves their quote.
        </p>
      )}
      {role === "operator" &&
        held &&
        allAccepted &&
        !voyage.accepted_economics.covers_modeled_costs && (
          <p className="line-note">
            This load does not cover the modeled sailing costs. Ask the
            coordinator for more compatible cargo or decline the departure.
          </p>
        )}
      {role === "operator" && held && (
        <div className="button-row">
          <button
            className="button primary"
            disabled={
              busy ||
              !allAccepted ||
              voyage.operator_accepted ||
              !voyage.accepted_economics.covers_modeled_costs
            }
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/operator-response`, role, {
                    version: voyage.version,
                    accept: true,
                  }),
                "Operator accepted the reviewed combined load and departure version.",
              )
            }
          >
            Accept reviewed departure
          </button>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/operator-response`, role, {
                    version: voyage.version,
                    accept: false,
                  }),
                "Operator declined. Local allocations released.",
              )
            }
          >
            Decline departure
          </button>
        </div>
      )}
      {voyage.members.map((member: Data) => (
        <div className="line-member" key={member.cargo_id}>
          <div>
            <h4>
              {title(member.cargo_type)} · {member.weight_tonnes} t
            </h4>
            <p>
              {member.origin} → {member.destination} · Door arrival{" "}
              {date(member.eta)}
            </p>
            <Badge value={member.status} />
            {member.booking_id && (
              <small>Customer reference {member.booking_id}</small>
            )}
          </div>
          {member.quote && (
            <div className="member-commercial">
              <strong className="line-price">
                {money(member.quote.total_cost)}
              </strong>
              <small>
                {member.accepted
                  ? "Approved delivery price"
                  : "Review this delivery price before approving"}
              </small>
              <details>
                <summary>Price breakdown and quote details</summary>
                <small>Locked quote {member.quote.id}</small>
                {Object.entries(
                  member.quote.snapshot.breakdown as Record<string, number>,
                ).map(([key, value]) => (
                  <div className="line-charge" key={key}>
                    <span>{title(key)}</span>
                    <strong>{money(value)}</strong>
                  </div>
                ))}
                <small>
                  Cards: {member.quote.snapshot.rate_card_ids.join(", ")}
                </small>
              </details>
              {member.invoice && (
                <small>
                  Invoice draft {member.invoice.id}:{" "}
                  {money(member.invoice.total)} · {member.invoice.status}
                </small>
              )}
              {role === "shipper" && held && (
                <button
                  className="button primary small"
                  disabled={busy || member.accepted}
                  onClick={() =>
                    act(
                      () =>
                        api(
                          `/lines/quotes/${member.quote.id}/approve`,
                          role,
                          {},
                        ),
                      "Exact quote version approved.",
                    )
                  }
                >
                  {member.accepted ? "Quote approved" : "Approve this quote"}
                </button>
              )}
            </div>
          )}
          {role === "shipper" &&
            confirmed &&
            ["CONFIRMED", "SCHEDULED"].includes(member.status) && (
              <button
                className="button small"
                disabled={busy}
                onClick={() =>
                  act(
                    () =>
                      api(`/lines/${voyage.id}/cancel`, role, {
                        cargo_id: member.cargo_id,
                      }),
                    "Cargo cancelled; other commitments and shared jobs retained.",
                  )
                }
              >
                Cancel this cargo
              </button>
            )}
          {role === "control" &&
            confirmed &&
            ["UNLOADING", "LAST_MILE"].includes(member.status) && (
              <ReceiptForm
                voyage={voyage}
                member={member}
                role={role}
                act={act}
                busy={busy}
              />
            )}
          {member.receipt && (
            <p className="muted">
              Receipt: {member.receipt.quantity_tonnes} t received by{" "}
              {member.receipt.receiver_name} · {member.receipt.source}
            </p>
          )}
        </div>
      ))}
      {role === "control" && (
        <details open={held} className="job-queue">
          <summary>
            <Truck size={16} /> Truck and terminal jobs · {voyage.jobs.length}{" "}
            assignments
          </summary>
          <p className="muted">
            Respond to each assigned job. The truck and terminal providers are
            simulated in this demo; a declined job releases the proposal.
          </p>
          {held &&
            switchRole &&
            voyage.jobs.some((job: Data) => job.status === "PENDING") && (
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    for (const job of voyage.jobs.filter(
                      (job: Data) => job.status === "PENDING",
                    ))
                      await api(`/lines/jobs/${job.id}/response`, role, {
                        status: "ACCEPTED",
                      });
                  }, "Every remaining provider acceptance recorded individually (simulated).")
                }
              >
                Simulate remaining provider acceptances
              </button>
            )}
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Job / resource</th>
                  <th>Window</th>
                  <th>Response</th>
                  <th>Coordinator action</th>
                </tr>
              </thead>
              <tbody>
                {[...voyage.jobs]
                  .sort(
                    (a: Data, b: Data) =>
                      a.starts_at.localeCompare(b.starts_at) ||
                      a.kind.localeCompare(b.kind),
                  )
                  .map((job: Data) => (
                    <tr key={job.id}>
                      <td>
                        {title(job.kind)}
                        <details>
                          <summary>Resource details · {job.source}</summary>
                          <small>
                            {job.truck_resource_id || job.terminal_resource_id}{" "}
                            · {job.source}
                          </small>
                        </details>
                        {job.provider_reference && (
                          <small>{job.provider_reference}</small>
                        )}
                      </td>
                      <td>
                        {date(job.starts_at)}
                        <small>to {date(job.ends_at)}</small>
                      </td>
                      <td>
                        <Badge value={job.status} />
                      </td>
                      <td>
                        {held && job.status === "PENDING" && (
                          <div className="button-row">
                            <button
                              className="button small"
                              aria-label={`Simulate accept ${title(job.kind)} ${job.id}`}
                              disabled={busy}
                              onClick={() =>
                                act(
                                  () =>
                                    api(
                                      `/lines/jobs/${job.id}/response`,
                                      role,
                                      {
                                        status: "ACCEPTED",
                                      },
                                    ),
                                  "Simulated provider acceptance recorded.",
                                )
                              }
                            >
                              Simulate accept
                            </button>
                            <button
                              className="button small"
                              aria-label={`Simulate decline ${title(job.kind)} ${job.id}`}
                              disabled={busy}
                              onClick={() =>
                                act(
                                  () =>
                                    api(
                                      `/lines/jobs/${job.id}/response`,
                                      role,
                                      {
                                        status: "DECLINED",
                                      },
                                    ),
                                  "Provider declined; remaining local allocations released.",
                                )
                              }
                            >
                              Simulate decline
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
      <div className="button-row">
        {["shipper", "control"].includes(role) && held && (
          <>
            <button
              className="button primary"
              disabled={busy || !canConfirm}
              onClick={() =>
                act(
                  () => api(`/lines/${voyage.id}/confirm`, role, {}),
                  "Delivery bundle confirmed at the accepted price.",
                )
              }
            >
              Confirm delivery bundle
            </button>
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  () => api(`/lines/${voyage.id}/cancel`, role, {}),
                  "Proposal cancelled. Local holds released.",
                )
              }
            >
              Cancel proposal
            </button>
          </>
        )}
        {role === "control" && confirmed && next && (
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/milestone`, role, { status: next }),
                "Shared milestone recorded (simulated).",
              )
            }
          >
            Record {title(next)}
          </button>
        )}
        {role === "control" &&
          confirmed &&
          ["CONFIRMED", "SCHEDULED"].includes(state) && (
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  () => api(`/lines/${voyage.id}/disrupt`, role, {}),
                  "Vessel withdrew before pickup. Original invoices voided; replacement requires fresh approvals.",
                )
              }
            >
              Simulate pre-pickup vessel withdrawal
            </button>
          )}
        {role === "control" && voyage.status === "DISRUPTED" && (
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              act(async () => {
                setAlternatives(
                  await api(`/lines/${voyage.id}/recovery-options`, role),
                );
              }, "Alternatives revalidated.")
            }
          >
            Find replacement departures
          </button>
        )}
      </div>
      <details className="departure-details">
        <summary>Departure reference and confirmation terms</summary>
        <p className="muted">
          {voyage.id} · Version {voyage.version}
        </p>
        <p className="muted">{voyage.commitment_policy}</p>
      </details>
      {alternatives && (
        <div className="line-note">
          <h4>Replacement offers need new owner and provider approvals</h4>
          {alternatives.options.length ? (
            alternatives.options.map((option: Data) => (
              <div className="replacement" key={option.vessel_id}>
                <span>
                  {option.vessel_name} · {date(option.departure)} ·{" "}
                  {money(option.total_cost)} combined
                </span>
                <button
                  className="button small"
                  disabled={busy}
                  onClick={() =>
                    act(
                      () =>
                        api("/lines/proposals", role, {
                          cargo_ids: option.cargo_ids,
                          vessel_id: option.vessel_id,
                          parent_id: voyage.id,
                        }),
                      "Replacement held. Owners must accept new quote versions before operators and providers confirm.",
                    )
                  }
                >
                  Request replacement quotes
                </button>
              </div>
            ))
          ) : (
            <p>No feasible replacement departure is available.</p>
          )}
        </div>
      )}
    </article>
  );
}

function ReceiptForm({ voyage, member, role, act, busy }: Data) {
  const [name, setName] = useState(""),
    [quantity, setQuantity] = useState(String(member.weight_tonnes));
  return (
    <form
      className="line-form receipt-form"
      onSubmit={(e) => {
        e.preventDefault();
        void act(
          () =>
            api(`/lines/${voyage.id}/receipt`, role, {
              cargo_id: member.cargo_id,
              quantity_tonnes: Number(quantity),
              receiver_name: name,
            }),
          "Individual door receipt recorded (simulated).",
        );
      }}
    >
      <label>
        Receiver name
        <input
          aria-label={`Receiver name ${member.cargo_id}`}
          required
          minLength={2}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label>
        Received tonnes
        <input
          aria-label={`Received tonnes ${member.cargo_id}`}
          type="number"
          required
          min=".001"
          max={member.weight_tonnes}
          step=".001"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
      </label>
      <button
        className="button primary small"
        disabled={busy || name.trim().length < 2}
      >
        Record door receipt
      </button>
    </form>
  );
}
