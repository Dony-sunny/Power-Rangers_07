import { useState } from "react";
import { api, type Act, type Data, title } from "../api";
import { Empty, Panel } from "./UI";
import { RateBenchmark } from "./NetworkIntelligence";
import LoadProfileReview from "./LoadProfileReview";

export default function FreightPlanning({
  data,
  role,
  act,
  busy,
  openPlanner,
}: {
  data: Data;
  role: string;
  act: Act;
  busy: boolean;
  openPlanner: (cargo: string) => void;
}) {
  const cargo = data.cargo.filter((item: Data) =>
    ["POSTED", "MATCHED", "QUOTED"].includes(item.status),
  );
  const [cargoId, setCargoId] = useState(cargo[0]?.id || "");
  const [vesselId, setVesselId] = useState(data.vessels[0]?.id || "");
  const [result, setResult] = useState<Data | null>(null);
  if (!cargo.length)
    return (
      <Empty>
        Post an unbooked load to evaluate matching, pooling and backhaul.
      </Empty>
    );
  return (
    <>
      <Panel
        title="Matching, pooling & backhaul"
        eyebrow="DETERMINISTIC PLANNING PREVIEWS"
      >
        <div className="form-content">
          <label className="field">
            Cargo
            <select
              value={cargoId}
              onChange={(e) => {
                setCargoId(e.target.value);
                setResult(null);
              }}
            >
              {cargo.map((item: Data) => (
                <option key={item.id} value={item.id}>
                  {title(item.cargo_type)} · {item.weight_tonnes} t ·{" "}
                  {item.origin} → {item.destination}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Boat
            <select
              value={vesselId}
              onChange={(e) => {
                setVesselId(e.target.value);
                setResult(null);
              }}
            >
              {data.vessels.map((item: Data) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="shipment-actions">
          <button
            className="button"
            disabled={busy || !cargoId}
            onClick={() =>
              act(
                async () =>
                  setResult(await api(`/cargo/${cargoId}/matches`, role)),
                "Matching evaluated.",
              )
            }
          >
            Evaluate matches
          </button>
          {[
            ["pool", "Find compatible pool"],
            ["backhaul", "Find return load"],
          ].map(([path, label]) => (
            <button
              key={path}
              className="button"
              disabled={busy || !cargoId || !vesselId}
              onClick={() =>
                act(
                  async () =>
                    setResult(
                      await api(
                        `/cargo/${cargoId}/${path}?vessel_id=${encodeURIComponent(vesselId)}`,
                        role,
                        {},
                      ),
                    ),
                  `${label} evaluated.`,
                )
              }
            >
              {label}
            </button>
          ))}
          <button
            className="button primary"
            onClick={() => openPlanner(cargoId)}
          >
            Review dated quote in marketplace
          </button>
        </div>
        <p className="role-intro">
          Planning results are previews. The marketplace reviews the complete
          load, resource availability and immutable delivered price before
          anyone commits.
        </p>
        {result && (
          <details open className="notice-list">
            <summary>Calculated result & reasons</summary>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                maxHeight: 480,
                overflow: "auto",
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        )}
      </Panel>
      <RateBenchmark role={role} cargoId={cargoId} vesselId={vesselId} />
      <LoadProfileReview
        key={cargoId}
        role={role}
        cargoId={cargoId}
        act={act}
        busy={busy}
      />
    </>
  );
}
