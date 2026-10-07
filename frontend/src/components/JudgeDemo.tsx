import { useState } from "react";
import { api, type Data, type Act, money, date } from "../api";
import { Panel, Badge, Stat } from "./UI";

const checkpoints = [
  [
    "VOICE",
    "Malayalam capacity",
    "Review transcript and approve the exact vessel window.",
  ],
  [
    "CARGO",
    "Document/text intake",
    "Review extracted construction cargo before creating demand.",
  ],
  [
    "FEASIBILITY",
    "Physical feasibility",
    "A strong commercial candidate fails draft; feasible alternatives remain.",
  ],
  [
    "OPTIMIZATION",
    "Pooling and return cargo",
    "Calculate 80 + 58 t and the compatible return opportunity.",
  ],
  [
    "BOOK",
    "Confirm real bookings",
    "Approve the shown pool and create shipments and manifests.",
  ],
  [
    "RECOVERY",
    "Optional disruption",
    "Compare replacement plans and approve whole-pool recovery.",
  ],
  [
    "START",
    "Begin the voyage",
    "Confirm operational milestones and simulated tracking progression.",
  ],
  [
    "IMPACT",
    "Government impact",
    "See metrics derived from those same bookings.",
  ],
];

export default function JudgeDemo({
  data,
  role,
  act,
  busy,
}: {
  data: Data;
  role: string;
  act: Act;
  busy: boolean;
}) {
  const [index, setIndex] = useState(0),
    [result, setResult] = useState<Data | null>(null),
    [approved, setApproved] = useState(false),
    [optionalRecovery, setOptionalRecovery] = useState(false),
    [option, setOption] = useState("pamba");
  if (!data.demo_mode) return null;
  const [stage, name, explanation] =
    checkpoints[Math.min(index, checkpoints.length - 1)];
  const consequential = [
    "VOICE",
    "CARGO",
    "BOOK",
    "RECOVERY",
    "START",
  ].includes(stage);
  const run = async (confirm: boolean) => {
    const evaluated = await api("/demo/judge/step", role, {
      stage,
      approved: confirm,
      vessel_id: stage === "RECOVERY" && confirm ? option : null,
    });
    setResult(evaluated);
    if (evaluated.complete) {
      setApproved(false);
      setIndex((i) => (i === 4 && !optionalRecovery ? 6 : i + 1));
    }
  };
  const payload = result?.result;
  return (
    <>
      <Panel
        title="Judge demo — the flagship journey"
        eyebrow="REAL WORKFLOW · EXPLICIT APPROVAL"
      >
        <div className="form-content">
          <p>
            Progress through visible checkpoints. Manual workspaces remain
            available. Data is synthetic; optimization and transaction results
            are computed.
          </p>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={optionalRecovery}
              onChange={(e) => setOptionalRecovery(e.target.checked)}
            />
            Include a simulated cancellation and replacement
          </label>
          <div className="judge-checkpoints">
            {checkpoints.map(([key, label], i) => (
              <div
                key={key}
                className={`judge-step ${i < index ? "complete" : i === index ? "current" : ""}`}
              >
                <span>{i + 1}</span>
                <strong>{label}</strong>
                <small>
                  {key === "RECOVERY"
                    ? "Optional checkpoint"
                    : i < index
                      ? "Completed"
                      : i === index
                        ? "Current"
                        : "Upcoming"}
                </small>
              </div>
            ))}
          </div>
          {index < checkpoints.length ? (
            <>
              <h3>{name}</h3>
              <p>{explanation}</p>
              {consequential && result?.stage === stage && !result.complete ? (
                <>
                  <label className="checkbox">
                    <input
                      type="checkbox"
                      checked={approved}
                      onChange={(e) => setApproved(e.target.checked)}
                    />
                    I approve the shown{" "}
                    {stage === "RECOVERY" ? "replacement plan" : "demo action"}.
                  </label>
                  {stage === "RECOVERY" && (
                    <label className="field">
                      Shown recovery option
                      <select
                        value={option}
                        onChange={(e) => setOption(e.target.value)}
                      >
                        {payload?.alternatives?.map((a: Data) => (
                          <option
                            value={a.vessel_id || ""}
                            key={a.vessel_id || a.mode}
                          >
                            {a.vessel_name} · {money(a.additional_cost)} · ETA{" "}
                            {date(a.plan.eta)}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <button
                    className="button primary"
                    disabled={busy || !approved}
                    onClick={() =>
                      act(() => run(true), "Checkpoint approved and persisted.")
                    }
                  >
                    Approve and continue
                  </button>
                </>
              ) : (
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() =>
                    act(
                      () => run(!consequential),
                      "Checkpoint calculated for review.",
                    )
                  }
                >
                  {consequential ? "Preview checkpoint" : "Run checkpoint"}
                </button>
              )}
            </>
          ) : (
            <div className="alert">
              Flagship journey completed. The government workspace reads these
              same records.
            </div>
          )}
          <button
            className="button danger"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await api("/demo/reset", role, {});
                setIndex(0);
                setResult(null);
                setApproved(false);
              }, "Fresh demo fixtures ready.")
            }
          >
            Reset judge story
          </button>
        </div>
      </Panel>
      {payload && (
        <Panel title="Computed checkpoint evidence">
          <div className="form-content">
            {payload.extraction && (
              <>
                <Badge
                  value={
                    payload.extraction.transcription_source?.includes("demo")
                      ? "DEMO TRANSCRIPT FALLBACK"
                      : payload.extraction.is_ai
                        ? "CONFIGURED AI"
                        : "LOCAL DETERMINISTIC EXTRACTION"
                  }
                />
                <div className="cost-details">
                  {Object.entries(payload.extraction.fields).map(
                    ([key, value]) => (
                      <div key={key}>
                        <span>{key.replaceAll("_", " ")}</span>
                        <strong>
                          {value === null
                            ? "Missing — confirm manually"
                            : String(value)}
                        </strong>
                      </div>
                    ),
                  )}
                </div>
                {payload.window && (
                  <p>
                    Exact approved window: {date(payload.window.available_from)}{" "}
                    to {date(payload.window.available_until)}
                  </p>
                )}
              </>
            )}
            {payload.recommendations && (
              <>
                <p>
                  {payload.recommendations.length} feasible options ·{" "}
                  {payload.rejected.length} hard rejections
                </p>
                {payload.rejected.map((r: Data) => (
                  <div className="alert" key={r.vessel_id}>
                    {r.vessel_name}: {r.feasibility.reasons.join("; ")}
                  </div>
                ))}
              </>
            )}
            {payload.mode_comparison && (
              <>
                <h3>Complete delivered mode comparison</h3>
                {payload.mode_comparison.plans.map((plan: Data) => (
                  <div className="service-card" key={plan.mode}>
                    <strong>{plan.mode}</strong>
                    <span>
                      {plan.feasible
                        ? `${money(plan.total_cost)} · ETA ${date(plan.eta)} · ${plan.emissions_kg} kg CO₂`
                        : plan.reasons.join(" ")}
                    </span>
                    <Badge value={plan.sla ? "SLA_PASS" : "UNAVAILABLE"} />
                  </div>
                ))}
                <p>
                  Recommended: {payload.mode_comparison.recommended_mode}.
                  Prices and emissions use disclosed synthetic assumptions.
                </p>
              </>
            )}
            {payload.pooling && (
              <div className="stats-row">
                <Stat
                  label="Before pooling"
                  value={`${payload.pooling.utilization_before_pct}%`}
                />
                <Stat
                  label="After pooling"
                  value={`${payload.pooling.utilization_after_pct}%`}
                />
                <Stat
                  label="Pool"
                  value={`${payload.pooling.total_tonnes} t`}
                />
                <Stat
                  label="Return cargo found"
                  value={`${payload.backhaul.opportunities.reduce((n: number, o: Data) => n + o.weight_tonnes, 0)} t`}
                />
              </div>
            )}
            {payload.bookings && (
              <p>
                {payload.bookings.length} bookings and shipments created in one
                transaction.
              </p>
            )}
            {payload.alternatives &&
              payload.alternatives.map((a: Data) => (
                <div className="service-card" key={a.vessel_id || a.mode}>
                  <div>
                    <h3>{a.vessel_name}</h3>
                    <p>
                      Old ETA {date(payload.old_plan?.eta)} → {date(a.plan.eta)}{" "}
                      · {money(a.additional_cost)} cost change ·{" "}
                      {a.eta_change_minutes} minutes
                    </p>
                    <small>{a.reason}</small>
                  </div>
                  <Badge value={a.sla ? "SLA_PASS" : "SLA_FAIL"} />
                </div>
              ))}
            {payload.recovered_count && (
              <p>
                {payload.recovered_count} pooled shipments recovered atomically.
              </p>
            )}
            {payload.shipments && (
              <p>
                {payload.shipments.length} shipments are now in transit.
                Positions are simulated.
              </p>
            )}
            {payload.tonnes_shifted !== undefined && (
              <div className="stats-row">
                <Stat
                  label="Confirmed modal shift"
                  value={`${payload.tonnes_shifted} t`}
                />
                <Stat
                  label="Estimated savings"
                  value={money(payload.cost_savings)}
                />
                <Stat
                  label="Estimated CO₂ avoided"
                  value={`${payload.co2_avoided_kg} kg`}
                />
                <Stat
                  label="Equivalent truck movements"
                  value={payload.truck_trips_potentially_avoided}
                />
              </div>
            )}
            {payload.explanation && <p>{payload.explanation}</p>}
            <small>{result?.source}</small>
          </div>
        </Panel>
      )}
    </>
  );
}
