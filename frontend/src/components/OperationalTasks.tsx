import { useState, useEffect } from "react";
import { api, type Data, type Act, date } from "../api";
import { Panel, Empty } from "./UI";

export default function OperationalTasks({
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
  const [values, setValues] = useState<Record<string, Data>>({});
  return (
    <Panel
      title={
        role === "fleet"
          ? "Voyage crew assignments"
          : "Handling completion & delays"
      }
    >
      {!data.shipments.length && <Empty>No assigned shipments yet.</Empty>}
      {data.shipments.map((item: Data) => {
        const id = item.shipment.id,
          fields = values[id] || {},
          update = (key: string, value: unknown) =>
            setValues((v) => ({ ...v, [id]: { ...fields, [key]: value } }));
        return (
          <div className="shipment-card" key={id}>
            <h3>
              {item.vessel_name} · {item.cargo.cargo_type} ·{" "}
              {item.cargo.weight_tonnes} t
            </h3>
            {role === "fleet" ? (
              <label className="field">
                Crew assignment
                <input
                  value={
                    fields.crew_assignment ??
                    item.shipment.operational_data?.crew_assignment ??
                    ""
                  }
                  onChange={(e) => update("crew_assignment", e.target.value)}
                />
              </label>
            ) : (
              <div className="form-grid">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={
                      fields.handling_completed ??
                      item.shipment.operational_data?.handling_completed ??
                      false
                    }
                    onChange={(e) =>
                      update("handling_completed", e.target.checked)
                    }
                  />
                  Handling complete
                </label>
                <label className="field">
                  Terminal delay (minutes)
                  <input
                    type="number"
                    min="0"
                    max="1440"
                    value={
                      fields.terminal_delay_minutes ??
                      item.shipment.operational_data?.terminal_delay_minutes ??
                      0
                    }
                    onChange={(e) =>
                      update("terminal_delay_minutes", Number(e.target.value))
                    }
                  />
                </label>
              </div>
            )}
            <button
              className="button"
              disabled={busy || !Object.keys(fields).length}
              onClick={() =>
                act(
                  () => api(`/shipments/${id}/operations`, role, fields),
                  "Operational assignment recorded.",
                )
              }
            >
              Save operational record
            </button>
            <small>
              Records support coordination. A delay does not silently change the
              approved voyage; dispatch reviews recovery separately.
            </small>
          </div>
        );
      })}
    </Panel>
  );
}

export function TruckAppointments({
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
  const [shipmentId, setShipmentId] = useState(
      data.shipments[0]?.shipment.id || "",
    ),
    [terminalId, setTerminalId] = useState(
      data.shipments[0]?.booking.origin_terminal_id || "",
    ),
    [carrier, setCarrier] = useState(""),
    [starts, setStarts] = useState(""),
    [ends, setEnds] = useState(""),
    [appointments, setAppointments] = useState<Data[]>([]),
    [error, setError] = useState("");
  const refresh = () =>
    api("/terminals/resources", role)
      .then((r) => setAppointments(r.truck_appointments))
      .catch((e) => setError(e.message));
  useEffect(() => {
    refresh();
  }, [role]);
  if (!["terminal", "dispatch", "control", "admin"].includes(role)) return null;
  const item = data.shipments.find((s: Data) => s.shipment.id === shipmentId),
    terminals = item
      ? [
          item.booking.origin_terminal_id,
          item.booking.destination_terminal_id,
        ].filter(Boolean)
      : [];
  return (
    <Panel title="Truck appointments & gate windows">
      {error && <div className="alert error">{error}</div>}
      {data.shipments.length ? (
        <div className="form-content">
          <div className="form-grid">
            <label className="field">
              Assigned shipment
              <select
                value={shipmentId}
                onChange={(e) => {
                  setShipmentId(e.target.value);
                  setTerminalId(
                    data.shipments.find(
                      (s: Data) => s.shipment.id === e.target.value,
                    )?.booking.origin_terminal_id || "",
                  );
                }}
              >
                {data.shipments.map((s: Data) => (
                  <option key={s.shipment.id} value={s.shipment.id}>
                    {s.cargo.cargo_type} · {s.cargo.weight_tonnes} t ·{" "}
                    {s.shipment.id}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Shipment terminal
              <select
                value={terminalId}
                onChange={(e) => setTerminalId(e.target.value)}
              >
                {terminals.map((id: string) => (
                  <option key={id} value={id}>
                    {data.terminals.find((t: Data) => t.id === id)?.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Carrier / truck reference
              <input
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
              />
            </label>
            <label className="field">
              Gate start (India time)
              <input
                type="datetime-local"
                value={starts}
                onChange={(e) => setStarts(e.target.value)}
              />
            </label>
            <label className="field">
              Gate end (India time)
              <input
                type="datetime-local"
                value={ends}
                onChange={(e) => setEnds(e.target.value)}
              />
            </label>
          </div>
          <button
            className="button primary"
            disabled={
              busy || !terminalId || carrier.length < 2 || !starts || !ends
            }
            onClick={() =>
              act(async () => {
                await api("/terminals/truck-appointments", role, {
                  shipment_id: shipmentId,
                  terminal_id: terminalId,
                  carrier,
                  starts_at: starts + ":00+05:30",
                  ends_at: ends + ":00+05:30",
                });
                await refresh();
              }, "Truck appointment and assignment recorded after gate collision check.")
            }
          >
            Reserve truck appointment
          </button>
        </div>
      ) : (
        <Empty>
          Book an assigned shipment before reserving its truck gate.
        </Empty>
      )}
      {appointments.map((a) => (
        <div className="service-card" key={a.id}>
          <strong>{a.carrier}</strong>
          <span>
            {date(a.starts_at)} → {date(a.ends_at)} · {a.gate_status}
          </span>
        </div>
      ))}
    </Panel>
  );
}
