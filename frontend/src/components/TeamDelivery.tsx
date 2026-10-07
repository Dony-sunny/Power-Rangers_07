import { useEffect, useState } from "react";
import { api, date, title, type Act, type Data } from "../api";
import { Badge, Empty, Panel } from "./UI";

const sequence = [
  "CONFIRMED",
  "SCHEDULED",
  "LOADING",
  "IN_TRANSIT",
  "UNLOADING",
];
export default function TeamDelivery({
  data,
  role,
  act,
  busy,
  setView,
}: {
  data: Data;
  role: string;
  act: Act;
  busy: boolean;
  setView: (view: string) => void;
}) {
  const [voyages, setVoyages] = useState<Data[]>([]);
  const [error, setError] = useState("");
  const [receipts, setReceipts] = useState<
    Record<string, { name?: string; quantity?: number }>
  >({});
  useEffect(() => {
    let active = true;
    api("/lines", role)
      .then((result) => {
        if (active) {
          setVoyages(result.departures);
          setError("");
        }
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [data, role]);
  return (
    <Panel
      title="Shared delivery operations"
      eyebrow="RECORDED WORKFLOW · SIMULATED EXECUTION"
    >
      {error && <p role="alert">{error}</p>}
      {!voyages.length && !error && (
        <Empty>
          No shared departures are assigned to this organization yet.
        </Empty>
      )}
      {voyages.map((voyage) => {
        const member = voyage.members.find(
          (item: Data) => !["CANCELLED", "DELIVERED"].includes(item.status),
        );
        const next = member && sequence[sequence.indexOf(member.status) + 1];
        return (
          <article className="shipment-card" key={voyage.id}>
            <div className="shipment-card-head">
              <h3>{voyage.vessel_name}</h3>
              <Badge value={voyage.status} />
            </div>
            <p>
              Service owner: {voyage.service_owner} · Water departure{" "}
              {date(voyage.departure)}
            </p>
            <p>{voyage.next_action}</p>
            {voyage.status === "CONFIRMED" &&
              next &&
              voyage.allowed_milestones.includes(next) && (
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() =>
                    act(
                      () =>
                        api(`/lines/${voyage.id}/milestone`, role, {
                          status: next,
                        }),
                      `Shared ${title(next)} recorded.`,
                    )
                  }
                >
                  Record shared {title(next)}
                </button>
              )}
            {voyage.members.map((item: Data) => {
              const fields = receipts[item.cargo_id] || {};
              const blocked =
                item.delivery_verification.required &&
                !item.delivery_verification.verified;
              return (
                <div className="shipment-card" key={item.cargo_id}>
                  <h4>
                    {title(item.cargo_type)} · {item.weight_tonnes} t ·{" "}
                    {item.origin} → {item.destination}
                  </h4>
                  <p>
                    Door ETA {date(item.eta)} · {title(item.status)}
                  </p>
                  {item.receipt && (
                    <p>
                      Received {item.receipt.quantity_tonnes} t by{" "}
                      {item.receipt.receiver_name}. Recorded by{" "}
                      {item.receipt.recorded_by}.
                    </p>
                  )}
                  {voyage.can_receive &&
                    ["UNLOADING", "LAST_MILE"].includes(item.status) && (
                      <>
                        {blocked && (
                          <p>
                            Verify the receiver code before recording this
                            receipt.{" "}
                            <button
                              className="text-button"
                              onClick={() => setView("evidence")}
                            >
                              Open delivery verification
                            </button>
                          </p>
                        )}
                        <div className="form-grid">
                          <label className="field">
                            Receiver name
                            <input
                              value={fields.name || ""}
                              onChange={(e) =>
                                setReceipts((old) => ({
                                  ...old,
                                  [item.cargo_id]: {
                                    ...fields,
                                    name: e.target.value,
                                  },
                                }))
                              }
                            />
                          </label>
                          <label className="field">
                            Quantity received (t)
                            <input
                              type="number"
                              min="0"
                              max={item.weight_tonnes}
                              step="0.01"
                              value={fields.quantity ?? item.weight_tonnes}
                              onChange={(e) =>
                                setReceipts((old) => ({
                                  ...old,
                                  [item.cargo_id]: {
                                    ...fields,
                                    quantity: Number(e.target.value),
                                  },
                                }))
                              }
                            />
                          </label>
                        </div>
                        <button
                          className="button primary"
                          disabled={
                            busy ||
                            blocked ||
                            (fields.name || "").trim().length < 2 ||
                            !Number.isFinite(
                              fields.quantity ?? item.weight_tonnes,
                            ) ||
                            (fields.quantity ?? item.weight_tonnes) <= 0 ||
                            (fields.quantity ?? item.weight_tonnes) >
                              item.weight_tonnes
                          }
                          onClick={() =>
                            act(
                              () =>
                                api(`/lines/${voyage.id}/receipt`, role, {
                                  cargo_id: item.cargo_id,
                                  quantity_tonnes:
                                    fields.quantity ?? item.weight_tonnes,
                                  receiver_name: fields.name!.trim(),
                                }),
                              "Individual delivery receipt recorded.",
                            )
                          }
                        >
                          Record individual receipt
                        </button>
                      </>
                    )}
                </div>
              );
            })}
          </article>
        );
      })}
    </Panel>
  );
}
