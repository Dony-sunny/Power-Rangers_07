import { useState, useEffect } from "react";
import { FileText, ArrowRight, RefreshCw } from "lucide-react";
import { api, type Data, type Act, date, money, title } from "../api";
import { Panel, Badge, Empty, Progress } from "./UI";
import RouteMap from "./RouteMap";

const sequence = [
  "CONFIRMED",
  "SCHEDULED",
  "LOADING",
  "IN_TRANSIT",
  "UNLOADING",
  "LAST_MILE",
  "DELIVERED",
];
export async function downloadDocument(
  bookingId: string,
  kind: string,
  role: string,
) {
  const doc = await api(`/bookings/${bookingId}/documents/${kind}`, role);
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `jalayatra-${kind}-${bookingId}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function Tracking({
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
  const [selected, setSelected] = useState(""),
    [tracking, setTracking] = useState<Data | null>(null),
    [recovery, setRecovery] = useState<Data | null>(null),
    [error, setError] = useState("");
  const [disruptionKind, setDisruptionKind] = useState("TRUCK_LATE");
  const current =
    data.shipments.find((s: Data) => s.shipment.id === selected) ||
    data.shipments[0];
  useEffect(() => {
    if (!current) return;
    api(`/shipments/${current.shipment.id}`, role)
      .then(setTracking)
      .catch((e) => setError(e.message));
  }, [current?.shipment.id, current?.shipment.status, role]);
  const canExecute = [
      "dispatch",
      "fleet",
      "captain",
      "terminal",
      "control",
      "admin",
    ].includes(role),
    canRecover = ["dispatch", "control", "admin"].includes(role);
  const next = (item: Data) => {
    const index = sequence.indexOf(item.shipment.status);
    return index < 0 || index === sequence.length - 1
      ? null
      : sequence[index + 1] === "LAST_MILE" && !item.cargo.last_mile_required
        ? "DELIVERED"
        : sequence[index + 1];
  };
  return (
    <>
      {canRecover && data.demo_mode && (
        <Panel title="Operational disruption simulation">
          <div className="form-content">
            <label className="field">
              Disruption type
              <select
                value={disruptionKind}
                onChange={(e) => setDisruptionKind(e.target.value)}
              >
                {[
                  "EQUIPMENT_UNAVAILABLE",
                  "SHIPMENT_NOT_READY",
                  "TRUCK_LATE",
                  "SERVICE_CANCELLED",
                  "CAPACITY_REDUCED",
                  "TERMINAL_CLOSED",
                ].map((kind) => (
                  <option key={kind}>{kind}</option>
                ))}
              </select>
            </label>
            <button
              className="button"
              disabled={
                busy ||
                !current ||
                !["CONFIRMED", "SCHEDULED"].includes(current.shipment.status)
              }
              onClick={() =>
                act(
                  async () =>
                    setRecovery(
                      await api(
                        `/bookings/${current.booking.id}/disrupt`,
                        role,
                        { kind: disruptionKind, delay_minutes: 60 },
                      ),
                    ),
                  "Disruption recorded; review revalidated alternatives.",
                )
              }
            >
              Simulate selected disruption
            </button>
            <small>
              Uses the selected shipment. Other records are preserved; affected
              bookings are identified before replanning.
            </small>
          </div>
        </Panel>
      )}
      {error && (
        <div className="alert error" role="alert">
          {error}
        </div>
      )}
      <div className="two-columns">
        <Panel
          title={
            role === "captain" ? "Your assigned voyages" : "Shipment execution"
          }
          eyebrow="ACTUAL WORKFLOW · SIMULATED POSITIONS"
        >
          {data.shipments.length ? (
            data.shipments.map((item: Data) => (
              <div key={item.shipment.id} className="shipment-card">
                <div className="shipment-card-head">
                  <h3>
                    {title(item.cargo.cargo_type)} · {item.cargo.weight_tonnes}{" "}
                    t
                  </h3>
                  <Badge value={item.shipment.status} />
                </div>
                <p>
                  {item.cargo.origin} → {item.cargo.destination} ·{" "}
                  {item.vessel_name}
                </p>
                <Progress value={item.shipment.progress} />
                <small>
                  ETA {date(item.booking.eta)} ·{" "}
                  {Math.round(item.shipment.progress * 100)}% milestone progress
                </small>
                <div className="shipment-actions">
                  <button
                    className="button small"
                    onClick={() => {
                      setSelected(item.shipment.id);
                      setRecovery(null);
                    }}
                  >
                    View timeline
                  </button>
                  <button
                    className="button small"
                    onClick={() =>
                      act(
                        () =>
                          downloadDocument(item.booking.id, "manifest", role),
                        "Manifest downloaded.",
                      )
                    }
                  >
                    <FileText size={13} />
                    Manifest
                  </button>
                  {canExecute && next(item) && (
                    <button
                      className="button primary small"
                      disabled={busy}
                      onClick={() =>
                        act(
                          () =>
                            api(
                              `/shipments/${item.shipment.id}/transition`,
                              role,
                              { status: next(item) },
                            ),
                          `Shipment advanced to ${title(next(item)!)}.`,
                        )
                      }
                    >
                      Confirm {title(next(item)!)}
                      <ArrowRight size={13} />
                    </button>
                  )}
                  {item.shipment.status === "DELIVERED" && (
                    <button
                      className="button small"
                      onClick={() =>
                        act(
                          () =>
                            downloadDocument(
                              item.booking.id,
                              "proof-of-delivery",
                              role,
                            ),
                          "Delivery record downloaded.",
                        )
                      }
                    >
                      Delivery record
                    </button>
                  )}
                </div>
                {canRecover &&
                  ["CONFIRMED", "SCHEDULED"].includes(item.shipment.status) && (
                    <div className="shipment-actions">
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() =>
                          act(async () => {
                            setSelected(item.shipment.id);
                            setRecovery(
                              await api(
                                `/bookings/${item.booking.id}/disrupt`,
                                role,
                                { kind: "VESSEL_UNAVAILABLE" },
                              ),
                            );
                          }, "Simulated cancellation. Review alternatives before approving.")
                        }
                      >
                        Simulate vessel cancellation
                      </button>
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() =>
                          act(async () => {
                            setSelected(item.shipment.id);
                            setRecovery(
                              await api(
                                `/bookings/${item.booking.id}/disrupt`,
                                role,
                                { kind: "ROUTE_CLOSED" },
                              ),
                            );
                          }, "Simulated route closure. Review recovery options.")
                        }
                      >
                        Simulate route closure
                      </button>
                    </div>
                  )}
                {canRecover && item.shipment.status === "REPLANNING" && (
                  <button
                    className="button small"
                    onClick={() =>
                      act(async () => {
                        setSelected(item.shipment.id);
                        setRecovery(
                          await api(
                            `/bookings/${item.booking.id}/recovery`,
                            role,
                          ),
                        );
                      }, "Recovery alternatives updated.")
                    }
                  >
                    <RefreshCw size={13} />
                    Review recovery
                  </button>
                )}
              </div>
            ))
          ) : (
            <Empty>
              No shipments yet. Confirm a booking from the shipper’s transport
              planner to begin execution.
            </Empty>
          )}
        </Panel>
        <div>
          <Panel
            title="Shipment positions"
            action={<span className="badge neutral">Simulated GPS</span>}
          >
            <RouteMap data={data} />
          </Panel>
          {tracking && (
            <Panel title="Shipment timeline">
              <div className="timeline">
                {tracking.events.map((e: Data) => (
                  <div key={e.id} className="timeline-item">
                    <strong>{title(e.status)}</strong>
                    <small>{date(e.timestamp)}</small>
                    <p>{e.description}</p>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
      {recovery && current && (
        <Panel
          title="Recovery requires your approval"
          eyebrow="REVALIDATED ALTERNATIVES"
        >
          <div className="role-intro">
            Approval changes this cargo’s vessel or mode and quote. Other pooled
            cargo requires separate approval.
          </div>
          {recovery.alternatives.map((a: Data) => (
            <div
              className="service-card"
              key={`${a.vessel_id || a.mode}-${a.service_id || "on-demand"}`}
            >
              <div>
                <h3>{a.vessel_name}</h3>
                <p>
                  {a.mode} · ETA {date(a.plan.eta)} · {money(a.additional_cost)}{" "}
                  cost change
                </p>
                <p>
                  Old ETA {date(recovery.old_plan?.eta)} → new ETA{" "}
                  {date(a.plan.eta)} · {a.eta_change_minutes} minutes ·{" "}
                  {a.reason}
                </p>
                <Badge value={a.sla ? "SLA_PASS" : "SLA_FAIL"} />
              </div>
              <button
                className="button primary"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    await api(`/bookings/${current.booking.id}/recover`, role, {
                      vessel_id: a.vessel_id,
                      mode: a.mode,
                      approved: true,
                      service_id: a.service_id || null,
                    });
                    setRecovery(null);
                  }, "Recovery approved and shipment rescheduled.")
                }
              >
                Approve {title(a.mode).toLowerCase()} recovery
              </button>
              {current.booking.pool_id && !a.service_id && (
                <button
                  className="button"
                  disabled={busy}
                  onClick={() =>
                    act(async () => {
                      await api(
                        `/bookings/${current.booking.id}/recover-pool`,
                        role,
                        {
                          vessel_id: a.vessel_id,
                          mode: a.mode,
                          approved: true,
                        },
                      );
                      setRecovery(null);
                    }, "Whole pool explicitly approved and revalidated on one replacement voyage.")
                  }
                >
                  Approve whole-pool recovery
                </button>
              )}
            </div>
          ))}
          {!recovery.alternatives.length && (
            <Empty>
              No replacement meets the deadline. Revise the request with the
              shipper.
            </Empty>
          )}
        </Panel>
      )}
    </>
  );
}
