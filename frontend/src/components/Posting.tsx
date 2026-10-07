import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Package,
  ShieldCheck,
} from "lucide-react";
import { api, date, title, type Cargo, type Data } from "../api";
const places = [
  "Kalamassery",
  "Kochi",
  "Maradu",
  "Vaikom",
  "Thanneermukkom",
  "Alappuzha",
];
const inputTime = (value: string) =>
  new Date(value)
    .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
    .replace(" ", "T")
    .slice(0, 16);
const iso = (value: string) => new Date(value + ":00+05:30").toISOString();
export default function Posting({
  data,
  role,
  cancel,
  done,
}: {
  data: Data;
  role: string;
  cancel: () => void;
  done: (cargo: Cargo) => Promise<void>;
}) {
  const [review, setReview] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [fields, setFields] = useState({
    cargo_type: "cement",
    weight_tonnes: "",
    volume_m3: "",
    packaging: "bagged",
    origin: "Kochi",
    destination: "Alappuzha",
    ready_time:
      inputTime(new Date(Date.now() + 86400000).toISOString()).slice(0, 10) +
      "T08:00",
    delivery_deadline:
      inputTime(new Date(Date.now() + 3 * 86400000).toISOString()).slice(
        0,
        10,
      ) + "T22:00",
    first_mile_required: true,
    last_mile_required: true,
    consolidation_allowed: true,
    heaviest_piece_tonnes: "0.05",
    pieces: "",
    unit_length_m: "1",
    unit_width_m: "1",
    unit_height_m: "1",
  });
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [review]);
  const update = (key: string, value: string | boolean) =>
    setFields((f) => {
      const next = { ...f, [key]: value };
      if (
        ["weight_tonnes", "heaviest_piece_tonnes", "cargo_type"].includes(key)
      ) {
        if (key === "cargo_type")
          next.heaviest_piece_tonnes = String(
            (
              {
                cement: 0.05,
                rice: 0.05,
                coir: 0.1,
                steel: 2,
                construction: 1,
                general: 1,
              } as Record<string, number>
            )[String(value)] || 1,
          );
        const weight = Number(next.weight_tonnes),
          piece = Number(next.heaviest_piece_tonnes);
        if (weight > 0 && piece > 0) {
          next.heaviest_piece_tonnes = String(Math.min(weight, piece));
          next.pieces = String(
            Math.ceil(weight / Number(next.heaviest_piece_tonnes)),
          );
        }
      }
      return next;
    });
  function sample() {
    const c = data.cargo.find((c: Cargo) => c.id === "hero-cargo");
    if (!c) return;
    setFields((f) => ({
      ...f,
      cargo_type: c.cargo_type,
      weight_tonnes: String(c.weight_tonnes),
      volume_m3: String(c.volume_m3),
      packaging: c.packaging,
      origin: c.origin,
      destination: c.destination,
      ready_time: inputTime(c.ready_time),
      delivery_deadline: inputTime(c.delivery_deadline),
      first_mile_required: c.first_mile_required,
      last_mile_required: c.last_mile_required,
      pieces: "1600",
    }));
  }
  function validate() {
    if (fields.origin === fields.destination)
      throw new Error("Choose different pickup and delivery locations.");
    if (iso(fields.delivery_deadline) <= iso(fields.ready_time))
      throw new Error("Delivery must be after your cargo is ready.");
    const weight = Number(fields.weight_tonnes),
      piece = Number(fields.heaviest_piece_tonnes),
      count = Number(fields.pieces);
    if (piece > weight || piece * count + 1e-9 < weight)
      throw new Error(
        "The number of pieces and weight of your heaviest piece must cover the total cargo weight.",
      );
  }
  async function submit() {
    setBusy(true);
    setError("");
    try {
      validate();
      const cargo = await api<Cargo>("/lines/cargo", role, {
        cargo: {
          cargo_type: fields.cargo_type,
          weight_tonnes: Number(fields.weight_tonnes),
          volume_m3: Number(fields.volume_m3),
          packaging: fields.packaging,
          origin: fields.origin,
          destination: fields.destination,
          ready_time: iso(fields.ready_time),
          delivery_deadline: iso(fields.delivery_deadline),
          first_mile_required: fields.first_mile_required,
          last_mile_required: fields.last_mile_required,
          consolidation_allowed: fields.consolidation_allowed,
        },
        load_profile: {
          heaviest_piece_tonnes: Number(fields.heaviest_piece_tonnes),
          pieces: Number(fields.pieces),
          unit_length_m: Number(fields.unit_length_m),
          unit_width_m: Number(fields.unit_width_m),
          unit_height_m: Number(fields.unit_height_m),
        },
      });
      await done(cargo);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="market-posting">
      <div className="market-page-heading">
        <div>
          <span className="market-kicker">CARGO POSTING</span>
          <h1>
            {review ? "Review your cargo" : "What would you like to send?"}
          </h1>
          <p>
            {review
              ? "Check the details below. Once posted, you can compare boats and plan a delivery."
              : "Add your cargo, route and dates. We’ll help you find a suitable boat."}
          </p>
        </div>
        <button className="button" onClick={cancel}>
          <ArrowLeft size={16} />
          Back to marketplace
        </button>
      </div>
      <div className="posting-layout">
        <section className="posting-form">
          {error && (
            <div role="alert" className="alert error">
              {error}
            </div>
          )}
          {review ? (
            <>
              <h2>
                <CheckCircle2 size={23} /> Ready to post
              </h2>
              <dl className="posting-summary">
                <div>
                  <dt>Cargo</dt>
                  <dd>
                    {title(fields.cargo_type)} · {fields.weight_tonnes} tonnes ·{" "}
                    {fields.volume_m3} m³
                  </dd>
                </div>
                <div>
                  <dt>Route</dt>
                  <dd>
                    {fields.origin} → {fields.destination}
                  </dd>
                </div>
                <div>
                  <dt>Ready for pickup</dt>
                  <dd>{date(iso(fields.ready_time))}</dd>
                </div>
                <div>
                  <dt>Deliver by</dt>
                  <dd>{date(iso(fields.delivery_deadline))}</dd>
                </div>
                <div>
                  <dt>Load</dt>
                  <dd>
                    {fields.pieces} pieces · Heaviest{" "}
                    {fields.heaviest_piece_tonnes} t<br />
                    {fields.unit_length_m} × {fields.unit_width_m} ×{" "}
                    {fields.unit_height_m} m largest piece
                  </dd>
                </div>
                <div>
                  <dt>Service</dt>
                  <dd>
                    {fields.first_mile_required
                      ? "Pickup truck included"
                      : "Pickup at terminal"}{" "}
                    ·{" "}
                    {fields.last_mile_required
                      ? "Delivery truck included"
                      : "Delivery to terminal"}
                    <br />
                    {fields.consolidation_allowed
                      ? "Can share a boat with compatible cargo"
                      : "Dedicated cargo only"}
                  </dd>
                </div>
              </dl>
              <div className="button-row">
                <button
                  className="button"
                  disabled={busy}
                  onClick={() => setReview(false)}
                >
                  Edit details
                </button>
                <button
                  className="button market-yellow"
                  disabled={busy}
                  onClick={submit}
                >
                  {busy ? "Posting…" : "Confirm & post cargo"}
                  <ArrowRight size={17} />
                </button>
              </div>
            </>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setError("");
                try {
                  validate();
                  setReview(true);
                } catch (err) {
                  setError((err as Error).message);
                }
              }}
            >
              <div className="posting-section-title">
                <h2>1. Cargo details</h2>
                {data.demo_mode && (
                  <button
                    type="button"
                    className="market-text-button"
                    onClick={sample}
                  >
                    Use cement sample
                  </button>
                )}
              </div>
              <div className="posting-fields">
                <label>
                  Goods to transport
                  <select
                    aria-label="Goods to transport"
                    value={fields.cargo_type}
                    onChange={(e) => update("cargo_type", e.target.value)}
                  >
                    {[
                      "cement",
                      "steel",
                      "construction",
                      "coir",
                      "rice",
                      "general",
                    ].map((c) => (
                      <option key={c} value={c}>
                        {title(c)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Packaging
                  <select
                    aria-label="Packaging"
                    value={fields.packaging}
                    onChange={(e) => update("packaging", e.target.value)}
                  >
                    {[
                      "bagged",
                      "bundled",
                      "bales",
                      "pallets",
                      "bulk",
                      "crates",
                    ].map((c) => (
                      <option key={c} value={c}>
                        {title(c)}
                      </option>
                    ))}
                  </select>
                </label>
                {[
                  ["weight_tonnes", "Total weight (tonnes)"],
                  ["volume_m3", "Total volume (m³)"],
                ].map(([k, label]) => (
                  <label key={k}>
                    {label}
                    <input
                      required
                      min="0.01"
                      step="any"
                      type="number"
                      value={fields[k as keyof typeof fields] as string}
                      onChange={(e) => update(k, e.target.value)}
                    />
                  </label>
                ))}
              </div>
              <h2>2. Route & dates</h2>
              <div className="posting-fields">
                {[
                  ["origin", "Pickup location"],
                  ["destination", "Delivery location"],
                ].map(([k, label]) => (
                  <label key={k}>
                    {label}
                    <select
                      aria-label={label}
                      value={fields[k as keyof typeof fields] as string}
                      onChange={(e) => update(k, e.target.value)}
                    >
                      {places.map((p) => (
                        <option key={p}>{p}</option>
                      ))}
                    </select>
                  </label>
                ))}
                {[
                  ["ready_time", "Ready for pickup"],
                  ["delivery_deadline", "Deliver by"],
                ].map(([k, label]) => (
                  <label key={k}>
                    {label}
                    <input
                      required
                      type="datetime-local"
                      value={fields[k as keyof typeof fields] as string}
                      onChange={(e) => update(k, e.target.value)}
                    />
                  </label>
                ))}
              </div>
              <p className="posting-hint">
                All dates and times use India Standard Time (IST).
              </p>
              <h2>3. Load size</h2>
              <p className="posting-hint">
                These details help us choose trucks, lifting equipment and a
                safe boat. The piece count is suggested from the weight of your
                heaviest piece. Check it against your actual load before
                posting.
              </p>
              <div className="posting-fields">
                {[
                  ["pieces", "Number of pieces"],
                  ["heaviest_piece_tonnes", "Heaviest piece (tonnes)"],
                  ["unit_length_m", "Largest piece length (m)"],
                  ["unit_width_m", "Largest piece width (m)"],
                  ["unit_height_m", "Largest piece height (m)"],
                ].map(([k, label]) => (
                  <label key={k}>
                    {label}
                    <input
                      required
                      type="number"
                      min={k === "pieces" ? "1" : "0.001"}
                      step={k === "pieces" ? "1" : "any"}
                      value={fields[k as keyof typeof fields] as string}
                      onChange={(e) => update(k, e.target.value)}
                    />
                  </label>
                ))}
              </div>
              <h2>4. Delivery preferences</h2>
              {[
                [
                  "first_mile_required",
                  "Include a truck from pickup location to the terminal",
                ],
                [
                  "last_mile_required",
                  "Include a truck from the terminal to delivery location",
                ],
                [
                  "consolidation_allowed",
                  "Allow compatible cargo to share the boat",
                ],
              ].map(([k, label]) => (
                <label key={k} className="posting-check">
                  <input
                    type="checkbox"
                    checked={fields[k as keyof typeof fields] as boolean}
                    onChange={(e) => update(k, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
              <button className="button market-yellow" type="submit">
                Review cargo
                <ArrowRight size={17} />
              </button>
            </form>
          )}
        </section>
        <aside className="posting-help">
          <Package size={32} />
          <h2>From posting to delivery</h2>
          <ol>
            <li>
              <strong>Post your cargo</strong>
              <p>Review your load and delivery details.</p>
            </li>
            <li>
              <strong>Compare boats & costs</strong>
              <p>See road and water delivery prices.</p>
            </li>
            <li>
              <strong>Plan a departure</strong>
              <p>Review dates and share capacity if suitable.</p>
            </li>
            <li>
              <strong>Approve & track</strong>
              <p>Approve your quote and follow the delivery.</p>
            </li>
          </ol>
          <p>
            <ShieldCheck size={17} /> Every booking passes cargo and route
            checks.
          </p>
        </aside>
      </div>
    </div>
  );
}
