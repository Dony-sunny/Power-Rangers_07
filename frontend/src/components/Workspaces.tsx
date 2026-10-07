import { useState, useEffect } from "react";
import { Plus, FileText } from "lucide-react";
import {
  api,
  type Data,
  type Cargo,
  type Act,
  money,
  date,
  title,
} from "../api";
import { Panel, Stat, Badge, Empty, TerminalTable } from "./UI";
import Intake from "./Intake";
import Tracking, { downloadDocument } from "./Tracking";
import Operator from "./Operator";
import Government from "./Government";
import {
  RecurringServices,
  FleetOptimization,
  TerminalResources,
} from "./Advanced";
import Evidence from "./Evidence";
import Administration from "./Administration";
import NetworkIntelligence from "./NetworkIntelligence";
import JudgeDemo from "./JudgeDemo";
import OperationalTasks, { TruckAppointments } from "./OperationalTasks";

type Props = {
  data: Data;
  role: string;
  view: string;
  act: Act;
  busy: boolean;
  setView: (view: string) => void;
};
export default function Workspaces(props: Props) {
  const { data, role, view, act, busy, setView } = props;
  if (view === "evidence") return <Evidence {...props} />;
  if (view === "judge") return <JudgeDemo {...props} />;
  if (view === "finance") return <Finance {...props} />;
  if (view === "administration") return <Administration {...props} />;
  if (view === "intelligence") return <NetworkIntelligence {...props} />;
  if (view === "optimization") return <FleetOptimization {...props} />;
  if (view === "resources")
    return (
      <>
        <TerminalResources {...props} />
        <TruckAppointments {...props} />
      </>
    );
  if (
    view === "tracking" ||
    (role === "captain" && view === "overview") ||
    role === "dispatch"
  )
    return <Tracking data={data} role={role} act={act} busy={busy} />;
  if (view === "voice")
    return (
      <Intake
        kind="vessel"
        data={data}
        role={role}
        done={() => act(async () => {}, "Availability saved.")}
        close={() => setView("overview")}
      />
    );
  if (view === "services")
    return (
      <>
        <Services {...props} />
        <RecurringServices {...props} />
      </>
    );
  if (view === "fleet" || role === "fleet")
    return (
      <>
        <Fleet {...props} />
        <OperationalTasks {...props} />
      </>
    );
  if (view === "reports") return <Reports {...props} />;
  if (view === "demo") return <Demo {...props} />;
  if (view === "audit") return <Audit data={data} />;
  if (["government", "network"].includes(role) || view === "intelligence")
    return <Government {...props} />;
  if (role === "operator")
    return <Operator data={data} role={role} setView={setView} />;
  if (role === "control") return <Control {...props} />;
  if (["warehouse", "receiver"].includes(role)) return <Handover {...props} />;
  if (role === "terminal")
    return (
      <>
        <Terminal {...props} />
        <OperationalTasks {...props} />
      </>
    );
  if (role === "finance") return <Finance {...props} />;
  if (role === "maintenance") return <Maintenance {...props} />;
  if (role === "compliance") return <Compliance {...props} />;
  if (role === "admin") return <Admin {...props} />;
  return <Empty>Select a workspace from navigation.</Empty>;
}

function Control(props: Props) {
  const { data, setView } = props;
  const risk = data.shipments.filter(
    (s: Data) =>
      s.booking.risk?.level === "HIGH" || s.shipment.status === "REPLANNING",
  );
  return (
    <>
      <div className="stats-row">
        <Stat
          label="Active shipments"
          value={
            data.shipments.filter(
              (s: Data) => s.shipment.status !== "DELIVERED",
            ).length
          }
        />
        <Stat label="Intervention required" value={risk.length} />
        <Stat
          label="Delivered shipments"
          value={
            data.shipments.filter(
              (s: Data) => s.shipment.status === "DELIVERED",
            ).length
          }
        />
        <Stat
          label="Unbooked requests"
          value={
            data.cargo.filter((c: Cargo) =>
              ["POSTED", "MATCHED", "QUOTED"].includes(c.status),
            ).length
          }
        />
      </div>
      <Panel
        title="Exception & SLA control"
        action={
          <button className="button primary" onClick={() => setView("planner")}>
            Plan multimodal cargo
          </button>
        }
      >
        {risk.length ? (
          risk.map((s: Data) => (
            <div className="shipment-card" key={s.shipment.id}>
              <h3>
                {s.cargo.origin} → {s.cargo.destination}
              </h3>
              <p>
                {s.cargo.weight_tonnes} t · {s.vessel_name} · ETA{" "}
                {date(s.booking.eta)}
              </p>
              <Badge value={s.shipment.status} />
              <button
                className="text-button"
                onClick={() => setView("tracking")}
              >
                Review intervention
              </button>
            </div>
          ))
        ) : (
          <Empty>
            No shipment currently needs intervention. Risk uses transparent
            deterministic factors.
          </Empty>
        )}
      </Panel>
      <Tracking {...props} />
    </>
  );
}

function Fleet({ data, role, act, busy }: Props) {
  const [show, setShow] = useState(false),
    [fields, setFields] = useState<Data>({
      name: "",
      max_capacity_tonnes: 150,
      max_volume_m3: 220,
      length: 38,
      beam: 7.5,
      loaded_draft: 1.5,
      air_draft: 4,
      current_location: "Maradu",
      cargo_categories: ["cement", "steel", "construction", "coir", "general"],
      rate_per_tonne_km: 3.2,
    });
  return (
    <>
      <Panel
        title="Fleet availability"
        action={
          <button className="button" onClick={() => setShow(!show)}>
            <Plus size={15} />
            Register vessel
          </button>
        }
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Vessel</th>
                <th>Capacity / volume</th>
                <th>Location</th>
                <th>Draft</th>
                <th>Compliance</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {data.vessels.map((v: Data) => (
                <tr key={v.id}>
                  <td>
                    <strong>{v.name}</strong>
                    <small>{v.vessel_type}</small>
                  </td>
                  <td>
                    {v.max_capacity_tonnes} t / {v.max_volume_m3} m³
                  </td>
                  <td>{v.current_location}</td>
                  <td>{v.loaded_draft} m</td>
                  <td>
                    <Badge value={v.compliance_status} />
                  </td>
                  <td>
                    <Badge value={v.state} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {show && (
          <div className="form-content">
            <div className="alert">
              New vessels require registration and insurance review in the
              compliance workspace before matching.
            </div>
            <div className="form-grid">
              {[
                "name",
                "max_capacity_tonnes",
                "max_volume_m3",
                "length",
                "beam",
                "loaded_draft",
                "air_draft",
                "current_location",
                "rate_per_tonne_km",
              ].map((k) => (
                <label className="field" key={k}>
                  {k.replace(/_/g, " ")}
                  <input
                    aria-label={`Vessel ${k}`}
                    type={
                      ["name", "current_location"].includes(k)
                        ? "text"
                        : "number"
                    }
                    value={fields[k]}
                    onChange={(e) =>
                      setFields((f) => ({
                        ...f,
                        [k]: ["name", "current_location"].includes(k)
                          ? e.target.value
                          : Number(e.target.value),
                      }))
                    }
                  />
                </label>
              ))}
            </div>
            <button
              className="button primary"
              disabled={busy || !fields.name}
              onClick={() =>
                act(async () => {
                  await api("/vessels", role, fields);
                  setShow(false);
                }, "Vessel registered; certificate review required.")
              }
            >
              Create vessel profile
            </button>
          </div>
        )}
      </Panel>
      <Intake
        kind="vessel"
        data={data}
        role={role}
        done={() => act(async () => {}, "Availability saved.")}
      />
      <Panel title="Listed operating windows">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Vessel</th>
                <th>Corridor</th>
                <th>From</th>
                <th>Until</th>
                <th>Capacity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.availability.map((a: Data) => (
                <tr key={a.id}>
                  <td>
                    {data.vessels.find((v: Data) => v.id === a.vessel_id)?.name}
                  </td>
                  <td>
                    {a.origin} → {a.destination}
                  </td>
                  <td>{date(a.available_from)}</td>
                  <td>{date(a.available_until)}</td>
                  <td>{a.capacity_tonnes} t</td>
                  <td>
                    <Badge value={a.active ? "AVAILABLE" : "CANCELLED"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function Services({ data, role, act, busy }: Props) {
  const [services, setServices] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [cargoId, setCargoId] = useState(
      data.cargo.find((c: Cargo) => c.id === "pool-cargo")?.id ||
        data.cargo[0]?.id ||
        "",
    );
  useEffect(() => {
    api("/services", role)
      .then(setServices)
      .catch((e) => setError(e.message));
  }, [role, data.shipments.length]);
  return (
    <Panel
      title="Scheduled freight capacity"
      eyebrow="BOOK TONNES ON A SHARED SERVICE"
    >
      {error && <div className="alert error">{error}</div>}
      <div className="form-content">
        <label className="field">
          Cargo to book
          <select
            aria-label="Scheduled cargo"
            value={cargoId}
            onChange={(e) => setCargoId(e.target.value)}
          >
            {data.cargo
              .filter((c: Cargo) =>
                ["POSTED", "MATCHED", "QUOTED"].includes(c.status),
              )
              .map((c: Cargo) => (
                <option key={c.id} value={c.id}>
                  {c.cargo_type} · {c.weight_tonnes} t · {c.origin} →{" "}
                  {c.destination}
                </option>
              ))}
          </select>
        </label>
      </div>
      {services?.services.map((s: Data) => (
        <div className="service-card" key={s.id}>
          <div>
            <h3>{s.name}</h3>
            <p>
              {s.recurrence} · Departure {date(s.departure)}
            </p>
            <p>
              {s.stops
                .map((stop: Data) =>
                  data.terminals
                    .find((t: Data) => t.id === stop.terminal_id)
                    ?.name.replace(" cargo terminal", ""),
                )
                .join(" → ")}
            </p>
            <Badge value="SCHEDULED" />
            <small>
              {s.remaining_capacity_tonnes} / {s.capacity_tonnes} t available on
              the busiest segment
            </small>
          </div>
          <button
            className="button primary"
            disabled={busy || !cargoId}
            onClick={() =>
              act(
                () =>
                  api("/bookings", role, {
                    cargo_id: cargoId,
                    vessel_id: s.vessel_id,
                    service_id: s.id,
                    mode: "HYBRID",
                    approved: true,
                  }),
                "Scheduled capacity confirmed. Shipment created.",
              )
            }
          >
            Approve capacity booking
          </button>
        </div>
      ))}
      {services && services.proposals.length > 0 && (
        <div className="notice-list">
          <h3>Demand-driven proposal</h3>
          {services.proposals.map((p: Data, i: number) => (
            <p key={i}>
              {p.origin} → {p.destination}: {p.requested_tonnes} t across{" "}
              {p.request_count} requests. {p.proposal}. Synthetic aggregate;
              confirm recurring demand before launch.
            </p>
          ))}
        </div>
      )}
    </Panel>
  );
}

function Handover({ data, role, act, busy }: Props) {
  const receiver = role === "receiver";
  const [values, setValues] = useState<Record<string, Data>>({});
  return (
    <Panel
      title={
        receiver
          ? "Incoming cargo & delivery acceptance"
          : "Upcoming loads & cargo verification"
      }
    >
      {data.shipments.length ? (
        data.shipments.map((item: Data) => {
          const f = values[item.shipment.id] || {},
            update = (key: string, value: unknown) =>
              setValues((v) => ({
                ...v,
                [item.shipment.id]: { ...f, [key]: value },
              }));
          return (
            <div className="shipment-card" key={item.shipment.id}>
              <div className="shipment-card-head">
                <h3>
                  {item.cargo.cargo_type} · {item.cargo.weight_tonnes} t
                </h3>
                <Badge value={item.shipment.status} />
              </div>
              <p>
                {item.cargo.origin} → {item.cargo.destination} · ETA{" "}
                {date(item.booking.eta)}
              </p>
              <div className="form-grid">
                {receiver ? (
                  <>
                    <label className="field">
                      Quantity received (t)
                      <input
                        type="number"
                        value={f.quantity_received_tonnes ?? ""}
                        onChange={(e) =>
                          update(
                            "quantity_received_tonnes",
                            Number(e.target.value),
                          )
                        }
                      />
                    </label>
                    <label className="field">
                      Receiver signature / name
                      <input
                        value={f.delivery_signature || ""}
                        onChange={(e) =>
                          update("delivery_signature", e.target.value)
                        }
                      />
                    </label>
                    <label className="field wide">
                      Damage / quantity discrepancy
                      <textarea
                        value={f.damage_report || ""}
                        onChange={(e) =>
                          update("damage_report", e.target.value)
                        }
                      />
                    </label>
                  </>
                ) : (
                  <>
                    <label className="field">
                      Actual weight (t)
                      <input
                        type="number"
                        value={
                          f.actual_weight_tonnes ?? item.cargo.weight_tonnes
                        }
                        onChange={(e) =>
                          update("actual_weight_tonnes", Number(e.target.value))
                        }
                      />
                    </label>
                    <label className="field">
                      Verified volume (m³)
                      <input
                        type="number"
                        value={f.actual_volume_m3 ?? item.cargo.volume_m3 ?? ""}
                        onChange={(e) =>
                          update("actual_volume_m3", Number(e.target.value))
                        }
                      />
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={f.packing_ready || false}
                        onChange={(e) =>
                          update("packing_ready", e.target.checked)
                        }
                      />
                      Packing complete
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={f.handover_confirmed || false}
                        onChange={(e) =>
                          update("handover_confirmed", e.target.checked)
                        }
                      />
                      Handover confirmed
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={f.gate_out || false}
                        onChange={(e) => update("gate_out", e.target.checked)}
                      />
                      Gate out recorded
                    </label>
                    <label className="field wide">
                      Loading sequence (one package per line)
                      <textarea
                        value={(f.loading_sequence || []).join("\n")}
                        onChange={(e) =>
                          update(
                            "loading_sequence",
                            e.target.value.split("\n").filter(Boolean),
                          )
                        }
                      />
                    </label>
                  </>
                )}
              </div>
              <div className="shipment-actions">
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() =>
                    act(
                      () =>
                        api(
                          `/shipments/${item.shipment.id}/operations`,
                          role,
                          receiver
                            ? f
                            : {
                                actual_weight_tonnes: item.cargo.weight_tonnes,
                                ...f,
                              },
                        ),
                      "Handover record saved.",
                    )
                  }
                >
                  Save{" "}
                  {receiver ? "delivery acceptance" : "loading verification"}
                </button>
                <button
                  className="button"
                  onClick={() =>
                    act(
                      () =>
                        downloadDocument(
                          item.booking.id,
                          receiver ? "delivery-note" : "loading-sheet",
                          role,
                        ),
                      "Document downloaded.",
                    )
                  }
                >
                  <FileText size={14} />
                  {receiver ? "Delivery note" : "Loading sheet"}
                </button>
              </div>
              <small>
                {receiver
                  ? `Receipt: ${item.shipment.operational_data?.delivery_signature || "awaiting receiver"}; ${item.shipment.operational_data?.quantity_received_tonnes ?? "unconfirmed"} t received.`
                  : `Packing ${item.shipment.operational_data?.packing_ready ? "complete" : "pending"}; handover ${item.shipment.operational_data?.handover_confirmed ? "confirmed" : "pending"}; gate out ${item.shipment.operational_data?.gate_out ? "recorded" : "pending"}.`}
              </small>
            </div>
          );
        })
      ) : (
        <Empty>
          No assigned loads yet. Book cargo from the shipper workspace.
        </Empty>
      )}
    </Panel>
  );
}

function Terminal({ data }: Props) {
  return (
    <>
      <div className="stats-row">
        <Stat label="Reserved berth windows" value={data.slots.length} />
        <Stat
          label="Incoming cargo"
          value={`${data.shipments.reduce((n: number, s: Data) => n + s.cargo.weight_tonnes, 0)} t`}
        />
        <Stat
          label="Open terminals"
          value={
            data.terminals.filter(
              (t: Data) => t.capability.operational_status === "OPEN",
            ).length
          }
        />
        <Stat
          label="Loading / unloading"
          value={
            data.shipments.filter((s: Data) =>
              ["LOADING", "UNLOADING"].includes(s.shipment.status),
            ).length
          }
        />
      </div>
      <Panel title="Berth & handling calendar">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Terminal</th>
                <th>Operation</th>
                <th>Window</th>
                <th>Booking</th>
              </tr>
            </thead>
            <tbody>
              {data.slots.map((s: Data) => (
                <tr key={s.id}>
                  <td>
                    {
                      data.terminals.find((t: Data) => t.id === s.terminal_id)
                        ?.name
                    }
                  </td>
                  <td>
                    <Badge value={s.operation} />
                  </td>
                  <td>
                    {date(s.starts_at)} → {date(s.ends_at)}
                  </td>
                  <td>{s.booking_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!data.slots.length && (
          <Empty>
            Booking automatically assigns non-conflicting loading and unloading
            windows.
          </Empty>
        )}
      </Panel>
      <Panel title="Equipment, storage & charges">
        <TerminalTable data={data} />
        <div className="metric-summary">
          {data.terminals.map((t: Data) => (
            <span key={t.id}>
              {t.name}: {money(t.handling_rate)} / tonne
            </span>
          ))}
        </div>
      </Panel>
    </>
  );
}

function Finance({ data, role, act, busy }: Props) {
  const [history, setHistory] = useState<Record<string, Data>>({});
  return (
    <>
      <div className="stats-row">
        <Stat label="Invoices" value={(data.invoices || []).length} />
        <Stat
          label="Booked total"
          value={money(
            (data.invoices || []).reduce(
              (n: number, i: Data) => n + i.total,
              0,
            ),
          )}
        />
        <Stat
          label="Pending payments"
          value={
            (data.payments || []).filter((p: Data) => p.status === "PENDING")
              .length
          }
        />
        <Stat
          label="Settled payouts"
          value={money(
            (data.payments || [])
              .filter((p: Data) => p.status === "SETTLED")
              .reduce((n: number, p: Data) => n + p.operator_payout, 0),
          )}
        />
      </div>
      <Panel title="Invoices & simulated settlements">
        {(data.payments || []).map((p: Data) => {
          const invoice = data.invoices.find(
            (i: Data) => i.id === p.invoice_id,
          );
          return (
            <div className="shipment-card" key={p.id}>
              <div className="shipment-card-head">
                <h3>
                  {money(p.amount)} · {invoice.booking_id}
                </h3>
                <Badge value={p.status} />
              </div>
              <p>Payout {money(p.operator_payout)} · demo 5% freight fee</p>
              <div className="cost-details">
                {Object.entries(invoice.line_items).map(([k, v]) => (
                  <div key={k}>
                    <span>{title(k)}</span>
                    <strong>{money(v as number)}</strong>
                  </div>
                ))}
              </div>
              <div className="shipment-actions">
                <button
                  className="button small"
                  onClick={() =>
                    act(
                      () =>
                        downloadDocument(invoice.booking_id, "invoice", role),
                      "Invoice draft downloaded.",
                    )
                  }
                >
                  Invoice draft
                </button>
                {["finance", "admin"].includes(role) &&
                  p.status === "PENDING" && (
                    <button
                      className="button primary small"
                      disabled={busy}
                      onClick={() =>
                        act(
                          () =>
                            api(`/payments/${p.id}/status`, role, {
                              status: "PAID",
                            }),
                          "Demo payment marked paid.",
                        )
                      }
                    >
                      Mark demo payment paid
                    </button>
                  )}
                {["finance", "admin"].includes(role) && p.status === "PAID" && (
                  <button
                    className="button primary small"
                    disabled={busy}
                    onClick={() =>
                      act(
                        () =>
                          api(`/payments/${p.id}/status`, role, {
                            status: "SETTLED",
                          }),
                        "Settlement recorded.",
                      )
                    }
                  >
                    Settle after delivery
                  </button>
                )}
                {["finance", "admin"].includes(role) &&
                  ["PENDING", "PAID"].includes(p.status) && (
                    <button
                      className="button small"
                      onClick={() =>
                        act(
                          () =>
                            api(`/payments/${p.id}/status`, role, {
                              status: "DISPUTED",
                              dispute: "Demo dispute raised for review",
                            }),
                          "Dispute recorded.",
                        )
                      }
                    >
                      Record dispute
                    </button>
                  )}
                {p.status === "DISPUTED" && (
                  <button
                    className="button"
                    disabled={busy}
                    onClick={() =>
                      act(
                        () =>
                          api(`/payments/${p.id}/status`, role, {
                            status: "PENDING",
                            dispute:
                              "Reviewed and resolved as prototype record",
                          }),
                        "Dispute resolved; payment returned to pending.",
                      )
                    }
                  >
                    Resolve prototype dispute
                  </button>
                )}
                <button
                  className="button small"
                  onClick={() =>
                    act(async () => {
                      const result = await api(
                        `/payments/${p.id}/history`,
                        role,
                      );
                      setHistory((h) => ({ ...h, [p.id]: result }));
                    }, "History refreshed.")
                  }
                >
                  Payment history
                </button>
              </div>
              {history[p.id] && (
                <div className="notice-list">
                  {history[p.id].events.map((e: Data) => (
                    <p key={e.id}>
                      {date(e.timestamp)} · {e.details.status || e.event}
                    </p>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {!data.payments?.length && (
          <Empty>
            Booking creates draft invoices and pending payments. No real payment
            provider is connected.
          </Empty>
        )}
      </Panel>
    </>
  );
}

function Maintenance({ data, role, act, busy }: Props) {
  const [defect, setDefect] = useState("");
  return (
    <Panel title="Defects, inspections & return to service">
      <div className="form-content">
        <label className="field">
          Defect / inspection note
          <textarea
            value={defect}
            onChange={(e) => setDefect(e.target.value)}
          />
        </label>
      </div>
      {data.vessels.map((v: Data) => {
        const m = data.maintenance.find((m: Data) => m.vessel_id === v.id);
        return (
          <div className="shipment-card" key={v.id}>
            <div className="shipment-card-head">
              <h3>{v.name}</h3>
              <Badge value={v.maintenance_status} />
            </div>
            <p>
              Inspection {m?.inspection_date || "Not recorded"} · Due{" "}
              {m?.due_date || "Not recorded"} ·{" "}
              {m?.defect || "No defects reported"}
            </p>
            <div className="shipment-actions">
              <button
                className="button danger"
                disabled={busy}
                onClick={() =>
                  act(
                    () =>
                      api(`/vessels/${v.id}/maintenance`, role, {
                        status: "DEFECT",
                        defect: defect || "Demo defect reported",
                      }),
                    "Vessel blocked from bookings.",
                  )
                }
              >
                Report defect & block booking
              </button>
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  act(
                    () =>
                      api(`/vessels/${v.id}/maintenance`, role, {
                        status: "OPERATIONAL",
                        defect,
                      }),
                    "Inspection recorded; vessel returned to service.",
                  )
                }
              >
                Confirm inspection & return to service
              </button>
            </div>
          </div>
        );
      })}
    </Panel>
  );
}

function Compliance({ data, role, act, busy }: Props) {
  const [vesselId, setVesselId] = useState(data.vessels[0]?.id || ""),
    [kind, setKind] = useState("REGISTRATION"),
    [expiry, setExpiry] = useState("");
  return (
    <>
      <Panel title="Certificates & pre-voyage trust">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Vessel</th>
                <th>Document</th>
                <th>Expiry</th>
                <th>Verification</th>
              </tr>
            </thead>
            <tbody>
              {data.certificates.map((c: Data) => (
                <tr key={c.id}>
                  <td>
                    {data.vessels.find((v: Data) => v.id === c.vessel_id)?.name}
                  </td>
                  <td>{title(c.kind)}</td>
                  <td>{date(c.expires_at)}</td>
                  <td>
                    <Badge value={c.verified ? "VERIFIED_PASS" : "PENDING"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="form-content">
          <div className="form-grid">
            <label className="field">
              Vessel
              <select
                value={vesselId}
                onChange={(e) => setVesselId(e.target.value)}
              >
                {data.vessels.map((v: Data) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Certificate type
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                {["REGISTRATION", "INSURANCE", "DANGEROUS_GOODS"].map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Expiry (India time)
              <input
                type="datetime-local"
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
              />
            </label>
          </div>
          <button
            className="button primary"
            disabled={busy || !expiry}
            onClick={() =>
              act(
                () =>
                  api(`/vessels/${vesselId}/certificates`, role, {
                    kind,
                    expires_at: expiry + ":00+05:30",
                    verified: true,
                  }),
                "Certificate review recorded.",
              )
            }
          >
            Record verified demo certificate
          </button>
          <small>
            Demo platform verification is not an official authority endorsement.
            Dangerous cargo remains subject to applicable compliance review.
          </small>
        </div>
      </Panel>
      <Audit data={data} />
    </>
  );
}

function Reports({ data, role, act, busy }: Props) {
  const [segment, setSegment] = useState(data.segments[0]?.id || ""),
    [type, setType] = useState("OBSTRUCTION"),
    [text, setText] = useState(""),
    [reviewNote, setReviewNote] = useState(""),
    [photos, setPhotos] = useState<Record<string, Data[]>>({});
  return (
    <Panel
      title="Navigation observations"
      eyebrow="OPERATOR REPORTS ARE UNVERIFIED"
    >
      <div className="form-content">
        <div className="form-grid">
          <label className="field">
            Waterway segment
            <select
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
            >
              {data.segments.map((s: Data) => (
                <option key={s.id}>{s.id}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Report type
            <select value={type} onChange={(e) => setType(e.target.value)}>
              {[
                "VEGETATION",
                "SHALLOW",
                "OBSTRUCTION",
                "DEBRIS",
                "DELAY",
                "HAZARD",
                "OTHER",
              ].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="field wide">
            Observation
            <textarea value={text} onChange={(e) => setText(e.target.value)} />
          </label>
        </div>
        <button
          className="button primary"
          disabled={busy || text.length < 3}
          onClick={() =>
            act(
              () =>
                api("/reports", role, {
                  segment_id: segment,
                  report_type: type,
                  description: text,
                  coordinates: (() => {
                    const node = data.nodes.find(
                      (n: Data) =>
                        n.id ===
                        data.segments.find((s: Data) => s.id === segment)
                          ?.source_node,
                    );
                    return [node.latitude, node.longitude];
                  })(),
                }),
              "Report stored as unverified.",
            )
          }
        >
          Submit observation
        </button>
      </div>
      {["admin", "network"].includes(role) && (
        <label className="field">
          Review reason
          <input
            value={reviewNote}
            onChange={(e) => setReviewNote(e.target.value)}
          />
        </label>
      )}
      {data.reports.map((r: Data) => (
        <div className="report-card" key={r.id}>
          <h3>
            {title(r.report_type)} · {r.segment_id}
          </h3>
          <p>{r.description}</p>
          <Badge value={r.verification_status} />
          <small>
            Expires {date(r.expires_at)} · no automatic official restriction
          </small>
          <div className="shipment-actions">
            {["admin", "network"].includes(role) &&
              ["VERIFIED", "DISPUTED"].map((status) => (
                <button
                  className="button small"
                  key={status}
                  disabled={busy || reviewNote.length < 3}
                  onClick={() =>
                    act(
                      () =>
                        api(
                          `/reports/${r.id}`,
                          role,
                          {
                            verification_status: status,
                            confidence: status === "VERIFIED" ? 0.8 : 0.2,
                            note: reviewNote,
                            promote_restriction: false,
                          },
                          "PATCH",
                        ),
                      "Platform review recorded.",
                    )
                  }
                >
                  {status === "VERIFIED"
                    ? "Verify observation"
                    : "Dispute observation"}
                </button>
              ))}
            {["admin", "network"].includes(role) &&
              r.verification_status === "VERIFIED" && (
                <button
                  className="button danger small"
                  disabled={busy || reviewNote.length < 3}
                  onClick={() =>
                    act(
                      () =>
                        api(
                          `/reports/${r.id}`,
                          role,
                          {
                            verification_status: "VERIFIED",
                            confidence: r.confidence,
                            note: reviewNote,
                            promote_restriction: true,
                          },
                          "PATCH",
                        ),
                      "Conservative temporary closure explicitly created.",
                    )
                  }
                >
                  Approve temporary restriction
                </button>
              )}
            <button
              className="button small"
              disabled={busy}
              onClick={() =>
                act(async () => {
                  const response = await api(`/reports/${r.id}/photos`, role);
                  setPhotos((p) => ({ ...p, [r.id]: response.photos }));
                }, "Observation photos loaded.")
              }
            >
              View observation photos
            </button>
            {(r.reporter_id === data.actor.id ||
              ["admin", "network"].includes(role)) && (
              <label className="field">
                Attach observation photo
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  disabled={busy}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file)
                      act(async () => {
                        const form = new FormData();
                        form.append("file", file);
                        await api(`/reports/${r.id}/photos`, role, form);
                      }, "Photo attached to observation.");
                  }}
                />
              </label>
            )}
          </div>
          {photos[r.id]?.map((photo) => (
            <img
              key={photo.id}
              src={photo.data_url}
              alt="Uploaded waterway observation"
              style={{ maxWidth: 240, maxHeight: 180 }}
            />
          ))}
        </div>
      ))}
    </Panel>
  );
}

function Audit({ data }: { data: Data }) {
  return (
    <Panel title="Audit trail">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Event</th>
              <th>Entity</th>
              <th>Actor</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {(data.audit || []).map((a: Data) => (
              <tr key={a.id}>
                <td>{a.event}</td>
                <td className="mono">{a.entity_id}</td>
                <td>{a.actor_id || "System"}</td>
                <td>{date(a.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!data.audit?.length && <Empty>No audited events yet.</Empty>}
    </Panel>
  );
}
function Demo({ act, busy }: Props) {
  const [result, setResult] = useState<Data | null>(null);
  const scenarios = [
    ["A", "Normal shipment", "Create a booking from the hero cargo."],
    [
      "B",
      "Hard constraint rejection",
      "Evaluate candidates and the draft failure.",
    ],
    ["C", "Compatible load pooling", "Calculate the 80 + 58 t OR-Tools pool."],
    ["D", "Find a return load", "Validate reverse corridor and time window."],
    [
      "E",
      "Cancellation & recovery",
      "Simulate cancellation and calculate alternatives.",
    ],
    ["F", "Flood resilience", "Toggle a simulated road restriction."],
  ];
  return (
    <Panel
      title="Deterministic demo controls"
      action={
        <button
          className="button danger"
          disabled={busy}
          onClick={() =>
            act(async () => {
              await api("/demo/reset", "admin", {});
              setResult(null);
            }, "Demo reset. Fresh fixtures ready.")
          }
        >
          Reset demo transactions
        </button>
      }
    >
      <div className="role-intro">
        Reset before each independent scenario. A creates a booking; E disrupts
        one. C calculates a preview that needs shipper approval to reserve.
      </div>
      <div className="demo-grid">
        {scenarios.map(([id, name, description]) => (
          <div className="demo-card" key={id}>
            <span className="badge neutral">SCENARIO {id}</span>
            <h3 style={{ marginTop: 12 }}>{name}</h3>
            <p>{description}</p>
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  async () =>
                    setResult(
                      await api("/demo/scenario", "admin", { scenario: id }),
                    ),
                  `Scenario ${id} evaluated.`,
                )
              }
            >
              Run scenario
            </button>
          </div>
        ))}
      </div>
      {result && (
        <details className="notice-list" open>
          <summary>Calculated result</summary>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontSize: 10,
              maxHeight: 400,
              overflow: "auto",
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        </details>
      )}
    </Panel>
  );
}
function Admin(props: Props) {
  const [health, setHealth] = useState<Data | null>(null);
  useEffect(() => {
    api("/health", "admin").then(setHealth);
  }, []);
  return (
    <>
      <div className="stats-row">
        <Stat
          label="Organizations"
          value={props.data.organizations?.length || 0}
        />
        <Stat label="Demo identities" value={props.data.users?.length || 0} />
        <Stat
          label="AI provider"
          value={health?.provider || "local"}
          note="Local fallback needs no credentials"
        />
        <Stat
          label="Operational data"
          value="Demo"
          note="Live integrations not connected"
        />
      </div>
      <Demo {...props} />
      <Panel title="Organization & role register">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Organization</th>
                <th>Type</th>
                <th>Trust</th>
              </tr>
            </thead>
            <tbody>
              {props.data.organizations?.map((o: Data) => (
                <tr key={o.id}>
                  <td>{o.name}</td>
                  <td>{o.kind}</td>
                  <td>
                    <Badge value={o.verified ? "VERIFIED_PASS" : "PENDING"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <Audit data={props.data} />
    </>
  );
}
