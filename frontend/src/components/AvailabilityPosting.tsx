import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Mic,
  Ship,
} from "lucide-react";
import { api, date, type Data } from "../api";
import { BoatArt } from "./Marketplace";
import Intake from "./Intake";
const places = [
  "Kalamassery",
  "Kochi",
  "Maradu",
  "Vaikom",
  "Thanneermukkom",
  "Alappuzha",
];
const localTime = (value: string) =>
  value
    ? new Date(value)
        .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
        .replace(" ", "T")
        .slice(0, 16)
    : "";
const iso = (value: string) => new Date(value + ":00+05:30").toISOString();
type Props = {
  data: Data;
  vesselId?: string;
  listingId?: string;
  register: () => void;
  cancel: () => void;
  done: (edited: boolean) => Promise<void>;
};
export default function AvailabilityPosting({
  data,
  vesselId,
  listingId,
  register,
  cancel,
  done,
}: Props) {
  const listing = data.availability.find((a: Data) => a.id === listingId);
  const [boatId, setBoatId] = useState(
    listing?.vessel_id ||
      (data.vessels.some((v: Data) => v.id === vesselId)
        ? vesselId
        : data.vessels[0]?.id) ||
      "",
  );
  const boat = data.vessels.find((v: Data) => v.id === boatId);
  const [mode, setMode] = useState("manual"),
    [review, setReview] = useState(false),
    [busy, setBusy] = useState(false);
  const [fields, setFields] = useState({
    origin: "",
    destination: "",
    available_from: "",
    available_until: "",
    capacity_tonnes: "",
    volume_m3: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({}),
    [serverError, setServerError] = useState("");
  const errorRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const existing =
      listing ||
      data.availability.find((a: Data) => a.vessel_id === boatId && a.active);
    setFields({
      origin: existing?.origin || "Kochi",
      destination: existing?.destination || "Alappuzha",
      available_from: localTime(existing?.available_from || ""),
      available_until: localTime(existing?.available_until || ""),
      capacity_tonnes: String(
        existing?.capacity_tonnes || boat?.max_capacity_tonnes || "",
      ),
      volume_m3: String(existing?.volume_m3 || boat?.max_volume_m3 || ""),
    });
    setErrors({});
    setServerError("");
  }, [boatId]);
  useEffect(() => {
    if (Object.keys(errors).length || serverError) errorRef.current?.focus();
  }, [errors, serverError]);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [review]);
  const update = (key: string, value: string) => {
    setFields((f) => ({ ...f, [key]: value }));
    setErrors((e) => {
      const copy = { ...e };
      delete copy[key];
      return copy;
    });
  };
  const labels: Record<string, string> = {
    origin: "Route from",
    destination: "Route to",
    available_from: "Available from (IST)",
    available_until: "Available until (IST)",
    capacity_tonnes: "Available capacity (tonnes)",
    volume_m3: "Available cargo volume (m³)",
  };
  function validate() {
    const next: Record<string, string> = {};
    for (const [key, label] of Object.entries(labels))
      if (!fields[key as keyof typeof fields])
        next[key] = `Enter ${label.toLowerCase()}.`;
    if (fields.origin === fields.destination)
      next.destination = "Choose a different destination.";
    if (
      fields.available_from &&
      fields.available_until &&
      iso(fields.available_until) <= iso(fields.available_from)
    )
      next.available_until = "Available until must be after the starting time.";
    for (const [key, max] of [
      ["capacity_tonnes", boat?.max_capacity_tonnes],
      ["volume_m3", boat?.max_volume_m3],
    ] as [string, number][]) {
      const value = Number(fields[key as keyof typeof fields]);
      if (!(value > 0) || value > max)
        next[key] = `Enter a value greater than zero and no more than ${max}.`;
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }
  async function save() {
    if (!validate()) return;
    setBusy(true);
    setServerError("");
    try {
      await api(
        listing ? `/availability/${listing.id}` : "/availability",
        "operator",
        {
          vessel_id: boatId,
          origin: fields.origin,
          destination: fields.destination,
          available_from: iso(fields.available_from),
          available_until: iso(fields.available_until),
          capacity_tonnes: Number(fields.capacity_tonnes),
          volume_m3: Number(fields.volume_m3),
        },
        listing ? "PUT" : "POST",
      );
      await done(Boolean(listing));
    } catch (e) {
      setServerError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!boat)
    return (
      <div className="operator-empty">
        <Ship size={30} />
        <h1>No registered boat available</h1>
        <p>
          Choose an operator account with a registered boat to publish
          availability.
        </p>
        <button className="button market-yellow" onClick={register}>
          Add a new boat
        </button>
      </div>
    );
  return (
    <div className="operator-posting">
      <div className="market-page-heading">
        <div>
          <span className="market-kicker">BOAT AVAILABILITY LISTING</span>
          <h1>
            {review
              ? "Review your boat listing"
              : listing
                ? "Edit boat availability"
                : "When is your boat available?"}
          </h1>
          <p>
            {listing
              ? "Update this route and window. Booked availability stays protected."
              : "Choose your boat, route and dates. Publish a listing for cargo owners to discover."}
          </p>
        </div>
        <button className="button" onClick={cancel}>
          <ArrowLeft size={16} />
          Back to my boats
        </button>
      </div>
      <div className="posting-layout">
        <section className="posting-form">
          {!listing && (
            <div className="availability-mode">
              <button
                className={mode === "manual" ? "selected" : ""}
                onClick={() => setMode("manual")}
              >
                Fill in details
              </button>
              <button
                className={mode === "voice" ? "selected" : ""}
                onClick={() => setMode("voice")}
              >
                <Mic size={16} />
                Voice / transcript
              </button>
            </div>
          )}
          {mode === "voice" ? (
            <Intake
              kind="vessel"
              initialTab="voice"
              initialVesselId={boatId}
              data={data}
              role="operator"
              done={() => done(false)}
            />
          ) : (
            <>
              {(Object.keys(errors).length > 0 || serverError) && (
                <div
                  className="availability-errors"
                  role="alert"
                  tabIndex={-1}
                  ref={errorRef}
                >
                  <strong>Check these details</strong>
                  {serverError && <p>{serverError}</p>}
                  <ul>
                    {Object.entries(errors).map(([key, message]) => (
                      <li key={key}>
                        <a href={`#availability-${key}`}>{message}</a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {review ? (
                <>
                  <h2>
                    <CheckCircle2 size={22} />
                    Ready to {listing ? "update" : "publish"}
                  </h2>
                  <dl className="posting-summary">
                    <div>
                      <dt>Boat</dt>
                      <dd>{boat.name}</dd>
                    </div>
                    <div>
                      <dt>Route</dt>
                      <dd>
                        {fields.origin} → {fields.destination}
                      </dd>
                    </div>
                    <div>
                      <dt>Available dates</dt>
                      <dd>
                        {date(iso(fields.available_from))}
                        <br />
                        to {date(iso(fields.available_until))}
                      </dd>
                    </div>
                    <div>
                      <dt>Available space</dt>
                      <dd>
                        {fields.capacity_tonnes} tonnes · {fields.volume_m3} m³
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
                      onClick={save}
                    >
                      {busy
                        ? "Saving…"
                        : listing
                          ? "Save availability changes"
                          : "Publish boat availability"}
                      <ArrowRight size={17} />
                    </button>
                  </div>
                </>
              ) : (
                <form
                  noValidate
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (validate()) setReview(true);
                  }}
                >
                  <h2>1. Choose your boat</h2>
                  {!listing && (
                    <button
                      type="button"
                      className="market-text-button"
                      onClick={register}
                    >
                      Add a new boat
                    </button>
                  )}
                  <label className="availability-boat-field">
                    Registered boat
                    <select
                      aria-label="Registered boat"
                      value={boatId}
                      disabled={Boolean(listing)}
                      onChange={(e) => setBoatId(e.target.value)}
                    >
                      {data.vessels.map((v: Data) => (
                        <option key={v.id} value={v.id}>
                          {v.name} · {v.max_capacity_tonnes} t
                        </option>
                      ))}
                    </select>
                  </label>
                  <h2>2. Route & dates</h2>
                  <div className="posting-fields">
                    {[
                      "origin",
                      "destination",
                      "available_from",
                      "available_until",
                    ].map((key) => (
                      <label key={key} htmlFor={`availability-${key}`}>
                        {labels[key]}
                        {key === "origin" || key === "destination" ? (
                          <select
                            id={`availability-${key}`}
                            value={fields[key]}
                            onChange={(e) => update(key, e.target.value)}
                            aria-invalid={Boolean(errors[key])}
                            aria-describedby={
                              errors[key] ? `error-${key}` : undefined
                            }
                          >
                            {places.map((p) => (
                              <option key={p}>{p}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            id={`availability-${key}`}
                            type="datetime-local"
                            value={fields[key as keyof typeof fields]}
                            onChange={(e) => update(key, e.target.value)}
                            aria-invalid={Boolean(errors[key])}
                            aria-describedby={
                              errors[key] ? `error-${key}` : undefined
                            }
                          />
                        )}
                        {errors[key] && (
                          <small
                            className="availability-field-error"
                            id={`error-${key}`}
                          >
                            {errors[key]}
                          </small>
                        )}
                      </label>
                    ))}
                  </div>
                  <p className="posting-hint">
                    Times are shown in India Standard Time. Include loading and
                    unloading time in your available window.
                  </p>
                  <h2>3. Space you can offer</h2>
                  <div className="posting-fields">
                    {["capacity_tonnes", "volume_m3"].map((key) => (
                      <label key={key} htmlFor={`availability-${key}`}>
                        {labels[key]}
                        <input
                          id={`availability-${key}`}
                          type="number"
                          min="0.01"
                          step="any"
                          value={fields[key as keyof typeof fields]}
                          onChange={(e) => update(key, e.target.value)}
                          aria-invalid={Boolean(errors[key])}
                          aria-describedby={
                            errors[key] ? `error-${key}` : undefined
                          }
                        />
                        {errors[key] && (
                          <small
                            className="availability-field-error"
                            id={`error-${key}`}
                          >
                            {errors[key]}
                          </small>
                        )}
                      </label>
                    ))}
                  </div>
                  <button className="button market-yellow">
                    Review availability
                    <ArrowRight size={17} />
                  </button>
                </form>
              )}
            </>
          )}
        </section>
        <aside className="posting-help operator-listing-help">
          <BoatArt />
          <h2>{boat.name}</h2>
          <p>
            {boat.max_capacity_tonnes} t maximum capacity
            <br />
            {boat.max_volume_m3} m³ maximum volume
          </p>
          <ol>
            <li>
              <strong>Publish availability</strong>
              <p>Cargo owners find your route and dates.</p>
            </li>
            <li>
              <strong>Review cargo requests</strong>
              <p>See the load, departure and approved revenue.</p>
            </li>
            <li>
              <strong>Accept & track</strong>
              <p>Accept a departure after cargo owners approve their quotes.</p>
            </li>
          </ol>
          <p>
            <CalendarDays size={16} /> Edit or pause unbooked windows from My
            boats.
          </p>
        </aside>
      </div>
    </div>
  );
}
