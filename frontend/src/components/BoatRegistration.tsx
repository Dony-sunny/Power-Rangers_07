import { useState } from "react";
import { ArrowLeft, ArrowRight, CheckCircle2, Ship } from "lucide-react";
import { api, date, type Data } from "../api";
const local = (value: Date) =>
  value
    .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
    .replace(" ", "T")
    .slice(0, 16);
const tomorrow = new Date(Date.now() + 86400000).toLocaleDateString("en-CA", {
  timeZone: "Asia/Kolkata",
});
const iso = (value: string) => new Date(value + ":00+05:30").toISOString();
export default function BoatRegistration({
  data,
  cancel,
  done,
}: {
  data: Data;
  cancel: () => void;
  done: (boatId: string) => Promise<void>;
}) {
  const [review, setReview] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [fields, setFields] = useState({
    name: "",
    capacity: "100",
    volume: "160",
    length: "38",
    beam: "7.5",
    draft: "1.3",
    air_draft: "3.8",
    rate: "3",
    origin: "Maradu",
    destination: "Alappuzha",
    available_from: tomorrow + "T08:00",
    available_until: local(
      new Date(new Date(tomorrow + "T08:00+05:30").getTime() + 7 * 86400000),
    ),
    demo_review: false,
  });
  const [categories, setCategories] = useState([
    "cement",
    "steel",
    "construction",
    "coir",
    "rice",
    "general",
  ]);
  const update = (key: string, value: string | boolean) =>
    setFields((f) => ({ ...f, [key]: value }));
  function validate() {
    if (!categories.length)
      throw new Error("Choose at least one supported cargo type.");
    if (fields.origin === fields.destination)
      throw new Error("Choose different route locations.");
    if (iso(fields.available_until) <= iso(fields.available_from))
      throw new Error("Availability must end after it starts.");
  }
  async function save() {
    setBusy(true);
    setError("");
    try {
      validate();
      const result = await api("/vessels/with-availability", "operator", {
        vessel: {
          name: fields.name,
          vessel_type: "BARGE",
          max_capacity_tonnes: Number(fields.capacity),
          max_volume_m3: Number(fields.volume),
          length: Number(fields.length),
          beam: Number(fields.beam),
          loaded_draft: Number(fields.draft),
          air_draft: Number(fields.air_draft),
          current_location: fields.origin,
          cargo_categories: categories,
          rate_per_tonne_km: Number(fields.rate),
        },
        availability: {
          origin: fields.origin,
          destination: fields.destination,
          available_from: iso(fields.available_from),
          available_until: iso(fields.available_until),
          capacity_tonnes: Number(fields.capacity),
          volume_m3: Number(fields.volume),
        },
        demo_certificate_review: fields.demo_review,
      });
      await done(result.vessel.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="operator-posting">
      <div className="market-page-heading">
        <div>
          <span className="market-kicker">REGISTER & LIST A BOAT</span>
          <h1>{review ? "Review your new boat" : "Add your boat"}</h1>
          <p>
            Enter your boat’s physical details and its first available route.
            Review before publishing.
          </p>
        </div>
        <button className="button" onClick={cancel}>
          <ArrowLeft size={16} />
          Back to my boats
        </button>
      </div>
      <section className="posting-form">
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        {review ? (
          <>
            <h2>
              <CheckCircle2 size={22} /> {fields.name}
            </h2>
            <dl className="posting-summary">
              <div>
                <dt>Capacity & rate</dt>
                <dd>
                  {fields.capacity} tonnes · {fields.volume} m³ · ₹{fields.rate}{" "}
                  / tonne-km
                </dd>
              </div>
              <div>
                <dt>Physical dimensions</dt>
                <dd>
                  {fields.length} m long × {fields.beam} m wide
                  <br />
                  Loaded draft {fields.draft} m · Air draft {fields.air_draft} m
                </dd>
              </div>
              <div>
                <dt>First availability</dt>
                <dd>
                  {fields.origin} → {fields.destination}
                  <br />
                  {date(iso(fields.available_from))} to{" "}
                  {date(iso(fields.available_until))}
                </dd>
              </div>
              <div>
                <dt>Supported cargo</dt>
                <dd>{categories.join(", ")}</dd>
              </div>
              <div>
                <dt>Certificate review</dt>
                <dd>
                  {fields.demo_review
                    ? "Simulated registration and insurance review for the local demo"
                    : "Pending certificate review; the boat cannot be booked until verified"}
                </dd>
              </div>
            </dl>
            <div className="button-row">
              <button
                className="button"
                onClick={() => setReview(false)}
                disabled={busy}
              >
                Edit details
              </button>
              <button
                className="button market-yellow"
                onClick={save}
                disabled={busy}
              >
                {busy ? "Saving…" : "Register & publish boat"}
                <ArrowRight size={16} />
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
                window.scrollTo({ top: 0, behavior: "instant" });
              } catch (err) {
                setError((err as Error).message);
              }
            }}
          >
            <h2>1. Boat details</h2>
            <div className="posting-fields">
              <label>
                Boat name
                <input
                  required
                  minLength={2}
                  maxLength={100}
                  value={fields.name}
                  onChange={(e) => update("name", e.target.value)}
                />
              </label>
              {[
                ["capacity", "Maximum capacity (tonnes)"],
                ["volume", "Cargo volume (m³)"],
                ["length", "Boat length (m)"],
                ["beam", "Boat width (m)"],
                ["draft", "Loaded draft (m)"],
                ["air_draft", "Air draft (m)"],
                ["rate", "Boat rate (₹ / tonne-km)"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    required
                    type="number"
                    min="0.01"
                    step="any"
                    value={fields[key as keyof typeof fields] as string}
                    onChange={(e) => update(key, e.target.value)}
                  />
                </label>
              ))}
            </div>
            <p className="posting-hint">
              The shown dimensions are example values. Replace them with your
              boat’s actual measurements.
            </p>
            <h2>2. Supported cargo</h2>
            <div className="boat-registration-categories">
              {[
                "cement",
                "steel",
                "construction",
                "coir",
                "rice",
                "general",
              ].map((c) => (
                <label className="posting-check" key={c}>
                  <input
                    type="checkbox"
                    checked={categories.includes(c)}
                    onChange={(e) =>
                      setCategories(
                        e.target.checked
                          ? [...categories, c]
                          : categories.filter((k) => k !== c),
                      )
                    }
                  />
                  {c}
                </label>
              ))}
            </div>
            <h2>3. First availability</h2>
            <div className="posting-fields">
              {[
                ["origin", "Route from"],
                ["destination", "Route to"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <select
                    aria-label={label}
                    value={fields[key as keyof typeof fields] as string}
                    onChange={(e) => update(key, e.target.value)}
                  >
                    {[
                      "Kochi",
                      "Maradu",
                      "Vaikom",
                      "Thanneermukkom",
                      "Alappuzha",
                    ].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
              ))}
              {[
                ["available_from", "Available from (IST)"],
                ["available_until", "Available until (IST)"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    required
                    type="datetime-local"
                    value={fields[key as keyof typeof fields] as string}
                    onChange={(e) => update(key, e.target.value)}
                  />
                </label>
              ))}
            </div>
            {data.demo_mode && (
              <label className="operator-shortfall-choice">
                <input
                  type="checkbox"
                  checked={fields.demo_review}
                  onChange={(e) => update("demo_review", e.target.checked)}
                />
                <span>
                  Use simulated registration and insurance review for this demo
                  boat.
                  <small>
                    No real certificates are verified. This option is available
                    only in demo mode.
                  </small>
                </span>
              </label>
            )}
            <button className="button market-yellow" type="submit">
              Review boat
              <ArrowRight size={16} />
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
