import { useEffect, useState } from "react";
import { api, type Data, type Act, money, date, title } from "../api";
import { Panel, Badge, Empty, Stat } from "./UI";

type Props = { data: Data; role: string; act: Act; busy: boolean };
const localTime = (value: string) =>
  new Date(value)
    .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
    .replace(" ", "T")
    .slice(0, 16);

export function RecurringServices({ data, role, act, busy }: Props) {
  const [snapshot, setSnapshot] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [selected, setSelected] = useState<string[]>([]),
    [cargo, setCargo] = useState("pool-cargo"),
    [contractId, setContractId] = useState("");
  const initial =
    data.services[0]?.departure?.slice(0, 10) ||
    new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState<Data>({
    name: "NW-3 recurring freight",
    template_service_id: "nw3-service",
    operating_days: [0, 2, 4],
    departure_time: "09:15",
    effective_date: initial,
    end_date: new Date(new Date(initial).getTime() + 14 * 86400000)
      .toISOString()
      .slice(0, 10),
    capacity_tonnes: 100,
    segment_capacities: {},
  });
  const [tonnes, setTonnes] = useState(60),
    [rate, setRate] = useState(300);
  const refresh = () =>
    api("/service-patterns", role)
      .then(setSnapshot)
      .catch((e) => setError(e.message));
  useEffect(() => {
    refresh();
  }, [role, data.shipments.length]);
  const update = (key: string, value: unknown) =>
    setForm((f) => ({ ...f, [key]: value }));
  const pattern = snapshot?.patterns[0];
  return (
    <Panel
      title="Recurring freight & committed capacity"
      eyebrow="DATED DEPARTURES · SEGMENT RESERVATIONS"
    >
      {error && <div className="alert error">{error}</div>}
      {["admin", "control", "fleet", "operator"].includes(role) && (
        <div className="form-content">
          <div className="form-grid">
            <label className="field">
              Service name
              <input
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
              />
            </label>
            <label className="field">
              Template service
              <select
                value={form.template_service_id}
                onChange={(e) => update("template_service_id", e.target.value)}
              >
                {data.services.map((s: Data) => (
                  <option value={s.id} key={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Departure (India time)
              <input
                type="time"
                value={form.departure_time}
                onChange={(e) => update("departure_time", e.target.value)}
              />
            </label>
            <label className="field">
              Capacity (t)
              <input
                type="number"
                min="1"
                value={form.capacity_tonnes}
                onChange={(e) =>
                  update("capacity_tonnes", Number(e.target.value))
                }
              />
            </label>
            <label className="field">
              Effective date
              <input
                type="date"
                value={form.effective_date}
                onChange={(e) => update("effective_date", e.target.value)}
              />
            </label>
            <label className="field">
              End date
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => update("end_date", e.target.value)}
              />
            </label>
          </div>
          <div className="shipment-actions">
            {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
              (day, index) => (
                <label className="checkbox" key={day}>
                  <input
                    type="checkbox"
                    checked={form.operating_days.includes(index)}
                    onChange={(e) =>
                      update(
                        "operating_days",
                        e.target.checked
                          ? [...form.operating_days, index]
                          : form.operating_days.filter(
                              (i: number) => i !== index,
                            ),
                      )
                    }
                  />
                  {day}
                </label>
              ),
            )}
          </div>
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await api("/service-patterns", role, form);
                await refresh();
              }, "Dated departures generated.")
            }
          >
            Generate recurring departures
          </button>
        </div>
      )}
      {snapshot?.patterns.map((p: Data) => (
        <div className="service-card" key={p.id}>
          <div>
            <h3>{p.name}</h3>
            <p>
              {p.operating_days
                .map(
                  (i: number) =>
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
                )
                .join(" / ")}{" "}
              · {p.departure_time} · {p.capacity_tonnes} t
            </p>
            <small>
              {p.effective_date} to {p.end_date} · {p.vessel_class}
            </small>
          </div>
          <Badge value={p.status} />
        </div>
      ))}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Select</th>
              <th>Departure date</th>
              <th>Status</th>
              <th>Occurrence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {snapshot?.occurrences.map((o: Data) => (
              <tr key={o.id}>
                <td>
                  <input
                    aria-label={`Select departure ${o.operating_date}`}
                    type="checkbox"
                    disabled={o.status !== "SCHEDULED"}
                    checked={selected.includes(o.service_id)}
                    onChange={(e) =>
                      setSelected(
                        e.target.checked
                          ? [...selected, o.service_id]
                          : selected.filter((id) => id !== o.service_id),
                      )
                    }
                  />
                </td>
                <td>{o.operating_date}</td>
                <td>
                  <Badge value={o.status} />
                </td>
                <td className="mono">{o.service_id}</td>
                <td>
                  {["admin", "control", "fleet", "operator"].includes(role) &&
                    o.status === "SCHEDULED" && (
                      <button
                        className="button small"
                        disabled={busy}
                        onClick={() =>
                          act(async () => {
                            await api(
                              `/services/${o.service_id}/cancel`,
                              role,
                              {},
                            );
                            await refresh();
                          }, "One occurrence cancelled; the pattern is preserved.")
                        }
                      >
                        Cancel occurrence
                      </button>
                    )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!snapshot?.occurrences.length && (
        <Empty>
          No generated departures yet. Fleet or control tower can create a dated
          pattern from the existing service.
        </Empty>
      )}
      {["shipper", "control", "admin"].includes(role) && (
        <div className="form-content">
          <div className="form-grid">
            <label className="field">
              Recurring cargo
              <select value={cargo} onChange={(e) => setCargo(e.target.value)}>
                {data.cargo
                  .filter((c: Data) =>
                    ["POSTED", "MATCHED", "QUOTED"].includes(c.status),
                  )
                  .map((c: Data) => (
                    <option value={c.id} key={c.id}>
                      {c.cargo_type} · {c.weight_tonnes} t · {c.id}
                    </option>
                  ))}
              </select>
            </label>
            <label className="field">
              Capacity contract
              <select
                value={contractId}
                onChange={(e) => setContractId(e.target.value)}
              >
                <option value="">Open market</option>
                {snapshot?.contracts.map((c: Data) => (
                  <option value={c.id} key={c.id}>
                    {c.tonnes_per_departure} t · {c.id}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p>
            Each selected departure creates a separate cargo occurrence with
            shifted readiness/deadline. All reservations succeed together or
            none are saved.
          </p>
          <button
            className="button primary"
            disabled={busy || !selected.length || !cargo}
            onClick={() =>
              act(async () => {
                await api("/services/recurring-bookings", role, {
                  cargo_id: cargo,
                  service_ids: selected,
                  contract_id: contractId || null,
                  approved: true,
                });
                setSelected([]);
                await refresh();
              }, "Recurring capacity explicitly approved and reserved.")
            }
          >
            Approve {selected.length} recurring reservations
          </button>
          {pattern && (
            <details className="notice-list">
              <summary>Reserve a prototype capacity contract</summary>
              <label className="field">
                Tonnes per departure
                <input
                  type="number"
                  value={tonnes}
                  onChange={(e) => setTonnes(Number(e.target.value))}
                />
              </label>
              <label className="field">
                Agreed rate per tonne (₹)
                <input
                  type="number"
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                />
              </label>
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    await api("/capacity-contracts", role, {
                      pattern_id: pattern.id,
                      start_date: pattern.effective_date,
                      end_date: pattern.end_date,
                      weekly_commitment_tonnes:
                        tonnes * pattern.operating_days.length,
                      tonnes_per_departure: tonnes,
                      rate_per_tonne: rate,
                      minimum_commitment_tonnes: tonnes,
                      start_sequence: 0,
                      end_sequence: pattern.stops.length - 1,
                    });
                    await refresh();
                  }, "Contract capacity held ahead of open-market bookings.")
                }
              >
                Approve capacity commitment
              </button>
              <small>
                Prototype commercial record; no legal contract is issued.
              </small>
            </details>
          )}
        </div>
      )}
    </Panel>
  );
}

export function FleetOptimization({ data, role, act, busy }: Props) {
  const [inventory, setInventory] = useState<Data | null>(null),
    [result, setResult] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [objective, setObjective] = useState("BALANCED"),
    [cargos, setCargos] = useState<string[]>([]),
    [vessels, setVessels] = useState<string[]>([]);
  useEffect(() => {
    api("/fleet/demand", role)
      .then((r) => {
        setInventory(r);
        setCargos(r.cargo.slice(0, 12).map((c: Data) => c.id));
        setVessels(r.vessels.map((v: Data) => v.id));
      })
      .catch((e) => setError(e.message));
  }, [role, data.shipments.length]);
  return (
    <>
      <Panel
        title="Fleet assignment optimizer"
        eyebrow="OR-TOOLS · HARD CONSTRAINTS BEFORE ASSIGNMENT"
      >
        {error && <div className="alert error">{error}</div>}
        <div className="form-content">
          <label className="field">
            Objective
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
            >
              {[
                "BALANCED",
                "MIN_COST",
                "MAX_UTILIZATION",
                "MIN_EMPTY",
                "ON_TIME",
              ].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </label>
          <p>
            One common-corridor voyage per vessel. Combined weight, volume,
            deadlines, terminals and cargo compatibility are revalidated.
          </p>
          <div className="two-column">
            <div>
              <h3>Available cargo</h3>
              {inventory?.cargo.map((c: Data) => (
                <label className="checkbox" key={c.id}>
                  <input
                    type="checkbox"
                    checked={cargos.includes(c.id)}
                    onChange={(e) =>
                      setCargos(
                        e.target.checked
                          ? [...cargos, c.id]
                          : cargos.filter((id) => id !== c.id),
                      )
                    }
                  />
                  {c.cargo_type} · {c.weight_tonnes} t · {c.origin} →{" "}
                  {c.destination}
                </label>
              ))}
            </div>
            <div>
              <h3>Vessels</h3>
              {inventory?.vessels.map((v: Data) => (
                <label className="checkbox" key={v.id}>
                  <input
                    type="checkbox"
                    checked={vessels.includes(v.id)}
                    onChange={(e) =>
                      setVessels(
                        e.target.checked
                          ? [...vessels, v.id]
                          : vessels.filter((id) => id !== v.id),
                      )
                    }
                  />
                  {v.name} · {v.max_capacity_tonnes} t
                </label>
              ))}
            </div>
          </div>
          <button
            className="button primary"
            disabled={busy || !cargos.length || !vessels.length}
            onClick={() =>
              act(
                async () =>
                  setResult(
                    await api("/fleet/optimize", role, {
                      cargo_ids: cargos,
                      vessel_ids: vessels,
                      objective,
                    }),
                  ),
                "Fleet assignment calculated; nothing booked yet.",
              )
            }
          >
            Optimize fleet assignment
          </button>
        </div>
      </Panel>
      {result && (
        <Panel
          title="Calculated fleet plan"
          action={<Badge value={result.solver_status} />}
        >
          <div className="form-content">
            <div className="stats-row">
              <Stat
                label="Utilization before"
                value={`${result.before.utilization_pct}%`}
              />
              <Stat
                label="Utilization after"
                value={`${result.after.utilization_pct}%`}
              />
              <Stat
                label="Estimated cost"
                value={money(result.after.estimated_cost)}
              />
              <Stat
                label="Unmatched cargo"
                value={result.after.unmatched_cargo}
              />
              <Stat
                label="Estimated cost before"
                value={money(result.before.estimated_cost)}
              />
              <Stat
                label="Empty repositioning"
                value={`${result.before.empty_reposition_km} → ${result.after.empty_reposition_km} km`}
              />
            </div>
            {result.assignments.map((a: Data) => (
              <div className="shipment-card" key={a.vessel_id}>
                <h3>
                  {a.vessel_name}: {a.tonnes} / {a.capacity_tonnes} t
                </h3>
                <p>
                  {a.cargo
                    .map((c: Data) => `${c.cargo_type} ${c.weight_tonnes} t`)
                    .join(" + ")}{" "}
                  · {a.utilization_pct}%
                </p>
                <p>{a.why.join(" ")}</p>
              </div>
            ))}
            <p>{result.source}</p>
            {["admin", "control"].includes(role) && (
              <button
                className="button primary"
                disabled={busy || !result.assignments.length}
                onClick={() =>
                  act(async () => {
                    await api(
                      `/fleet/plans/${result.plan_id}/approve?approved=true`,
                      role,
                      {},
                    );
                    setResult(null);
                  }, "Fleet bookings approved and revalidated atomically.")
                }
              >
                Approve and revalidate fleet bookings
              </button>
            )}
          </div>
        </Panel>
      )}
    </>
  );
}

export function TerminalResources({ data, role, act, busy }: Props) {
  const [snapshot, setSnapshot] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [resourceId, setResourceId] = useState(""),
    [starts, setStarts] = useState(""),
    [ends, setEnds] = useState(""),
    [quantity, setQuantity] = useState(1),
    [name, setName] = useState("Jetty 2"),
    [terminalId, setTerminalId] = useState(data.terminals[0]?.id || ""),
    [kind, setKind] = useState("BERTH");
  const refresh = () =>
    api("/terminals/resources", role)
      .then((r) => {
        setSnapshot(r);
        setResourceId((id) => id || r.resources[0]?.id || "");
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    refresh();
  }, [role, data.slots.length]);
  return (
    <Panel
      title="Terminal resources & queue"
      eyebrow="BERTH · EQUIPMENT · STORAGE · TRUCK GATE"
    >
      {error && <div className="alert error">{error}</div>}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Resource</th>
              <th>Capacity</th>
              <th>Availability</th>
            </tr>
          </thead>
          <tbody>
            {snapshot?.resources.map((r: Data) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>
                  {r.capacity}
                  {r.kind === "STORAGE" ? " t" : " units"}
                </td>
                <td>
                  <Badge value={r.active ? "AVAILABLE" : "UNAVAILABLE"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Queue / resource</th>
              <th>Start</th>
              <th>End</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            {snapshot?.reservations.map((r: Data) => (
              <tr key={r.id}>
                <td>
                  {
                    snapshot.resources.find((x: Data) => x.id === r.resource_id)
                      ?.name
                  }
                </td>
                <td>{date(r.starts_at)}</td>
                <td>{date(r.ends_at)}</td>
                <td>{r.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {["terminal", "control", "admin"].includes(role) && (
        <div className="form-content">
          <h3>Reserve a resource window</h3>
          <div className="form-grid">
            <label className="field">
              Resource
              <select
                value={resourceId}
                onChange={(e) => setResourceId(e.target.value)}
              >
                {snapshot?.resources.map((r: Data) => (
                  <option value={r.id} key={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Quantity
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
              />
            </label>
            <label className="field">
              Start (India time)
              <input
                type="datetime-local"
                value={starts}
                onChange={(e) => setStarts(e.target.value)}
              />
            </label>
            <label className="field">
              End (India time)
              <input
                type="datetime-local"
                value={ends}
                onChange={(e) => setEnds(e.target.value)}
              />
            </label>
          </div>
          <button
            className="button primary"
            disabled={busy || !starts || !ends}
            onClick={() =>
              act(async () => {
                await api("/terminals/reservations", role, {
                  resource_id: resourceId,
                  starts_at: starts + ":00+05:30",
                  ends_at: ends + ":00+05:30",
                  quantity,
                  description: "Operational reservation",
                });
                await refresh();
              }, "Resource reserved after collision check.")
            }
          >
            Check and reserve slot
          </button>
          <details className="notice-list">
            <summary>Add a terminal resource</summary>
            <div className="form-grid">
              <label className="field">
                Terminal
                <select
                  value={terminalId}
                  onChange={(e) => setTerminalId(e.target.value)}
                >
                  {data.terminals.map((t: Data) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                Name
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label className="field">
                Kind
                <select value={kind} onChange={(e) => setKind(e.target.value)}>
                  {["BERTH", "CRANE", "FORKLIFT", "STORAGE", "TRUCK_GATE"].map(
                    (k) => (
                      <option key={k}>{k}</option>
                    ),
                  )}
                </select>
              </label>
            </div>
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(async () => {
                  await api("/terminals/resources", role, {
                    terminal_id: terminalId,
                    name,
                    kind,
                    capacity: kind === "STORAGE" ? 500 : 1,
                    max_vessel_length: 70,
                  });
                  await refresh();
                }, "Resource added.")
              }
            >
              Add resource
            </button>
          </details>
        </div>
      )}
    </Panel>
  );
}
