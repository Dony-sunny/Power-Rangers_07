import { useState, useRef, useEffect } from "react";
import {
  Mic,
  FileText,
  Package,
  X,
  Square,
  Upload,
  Check,
  Keyboard,
} from "lucide-react";
import { api, download, type Data, type Cargo } from "../api";
import { Panel, Badge } from "./UI";

const places = [
  "Kalamassery",
  "Kochi",
  "Maradu",
  "Vaikom",
  "Thanneermukkom",
  "Alappuzha",
];
const sample =
  "80 tonnes of cement, bagged, 60 m3, from Kalamassery to Alappuzha. Ready tomorrow 08:00; deliver by tomorrow 22:00. Non-hazardous.";
const voiceSample = "Nale 150 ton barge Kochi-ninnu Alappuzha-kku kaali aanu.";
const inputTime = (value: string) =>
  value
    ? new Date(value)
        .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
        .replace(" ", "T")
        .slice(0, 16)
    : "";
const isoTime = (value: string) =>
  new Date(value.length === 16 ? value + ":00+05:30" : value).toISOString();

export default function Intake({
  kind = "cargo",
  initialTab,
  initialVesselId,
  data,
  role,
  done,
  close,
}: {
  kind?: "cargo" | "vessel";
  initialTab?: string;
  initialVesselId?: string;
  data: Data;
  role: string;
  done: (created?: Cargo) => void | Promise<void>;
  close?: () => void;
}) {
  const [tab, setTab] = useState(
      initialTab || (kind === "cargo" ? "text" : "voice"),
    ),
    [text, setText] = useState(kind === "cargo" ? sample : voiceSample),
    [extraction, setExtraction] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [file, setFile] = useState<File | null>(null),
    [useDemo, setUseDemo] = useState(false),
    [recording, setRecording] = useState(false),
    [vesselId, setVesselId] = useState(
      initialVesselId || data.vessels[0]?.id || "",
    ),
    [bulk, setBulk] = useState<Data | null>(null);
  const [fields, setFields] = useState<Data>({
    cargo_type: "",
    weight_tonnes: "",
    volume_m3: "",
    packaging: "",
    origin: "",
    destination: "",
    ready_time: "",
    delivery_deadline: "",
    capacity_tonnes: "",
    available_from: "",
    available_until: "",
    first_mile_required: true,
    last_mile_required: false,
    consolidation_allowed: true,
    hazardous: false,
    fragile: false,
    perishable: false,
    temperature_control_required: false,
  });
  useEffect(() => {
    if (kind !== "vessel" || tab !== "manual") return;
    const vessel = data.vessels.find((v: Data) => v.id === vesselId);
    const listing = data.availability.find(
      (a: Data) => a.vessel_id === vesselId,
    );
    setFields((f) => ({
      ...f,
      capacity_tonnes: String(
        listing?.capacity_tonnes || vessel?.max_capacity_tonnes || "",
      ),
      origin: listing?.origin || "Kochi",
      destination: listing?.destination || "Alappuzha",
      available_from: inputTime(listing?.available_from || ""),
      available_until: inputTime(listing?.available_until || ""),
    }));
  }, [kind, tab, vesselId]);
  const recorder = useRef<MediaRecorder | null>(null),
    stream = useRef<MediaStream | null>(null),
    chunks = useRef<Blob[]>([]);
  useEffect(
    () => () => {
      stream.current?.getTracks().forEach((t) => t.stop());
    },
    [],
  );
  const update = (key: string, value: unknown) =>
    setFields((f) => ({ ...f, [key]: value }));
  function review(result: Data) {
    setExtraction(result);
    const parsed: Data = {};
    for (const [key, value] of Object.entries(result.fields))
      parsed[key] =
        value == null
          ? [
              "fragile",
              "hazardous",
              "perishable",
              "temperature_control_required",
            ].includes(key)
            ? false
            : ""
          : key.endsWith("_time") ||
              key.endsWith("_deadline") ||
              (key.startsWith("available_") && key !== "available_date")
            ? inputTime(value as string)
            : value;
    setFields((f) => ({
      ...Object.fromEntries(
        Object.keys(f).map((k) => [k, typeof f[k] === "boolean" ? f[k] : ""]),
      ),
      ...parsed,
    }));
    if (kind === "vessel") {
      const availability = data.availability.find(
        (a: Data) => a.vessel_id === vesselId,
      );
      setFields((f) => ({
        ...f,
        available_from: result.fields.available_from
          ? inputTime(result.fields.available_from)
          : inputTime(availability?.available_from || ""),
        available_until: result.fields.available_until
          ? inputTime(result.fields.available_until)
          : inputTime(availability?.available_until || ""),
      }));
    }
  }
  async function parse(demo = false) {
    setBusy(true);
    setError("");
    try {
      if (kind === "vessel" && demo) {
        review(await api("/intake/vessel/demo", role, {}));
        return;
      }
      if (tab === "document" || (file && kind === "vessel")) {
        if (!file) throw new Error("Choose a file to upload.");
        const form = new FormData();
        form.append("file", file);
        if (kind === "vessel")
          form.append("use_demo_transcript", String(useDemo));
        const result = await api(
          kind === "cargo" && tab === "bulk"
            ? "/intake/cargo/bulk-preview"
            : kind === "cargo"
              ? "/intake/cargo/document"
              : "/intake/vessel/audio",
          role,
          form,
        );
        review(result);
      } else if (tab === "bulk") {
        if (!file) throw new Error("Choose a CSV file.");
        const form = new FormData();
        form.append("file", file);
        setBulk(await api("/intake/cargo/bulk-preview", role, form));
      } else review(await api(`/intake/${kind}/text`, role, { text }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    setBusy(true);
    setError("");
    try {
      let createdCargo: Cargo | undefined;
      if (kind === "cargo") {
        const payload = { ...fields };
        for (const key of [
          "capacity_tonnes",
          "available_from",
          "available_until",
          "available_date",
          "vessel_type",
        ])
          delete payload[key];
        payload.weight_tonnes = Number(payload.weight_tonnes);
        payload.volume_m3 = payload.volume_m3
          ? Number(payload.volume_m3)
          : null;
        payload.ready_time = isoTime(payload.ready_time);
        payload.delivery_deadline = isoTime(payload.delivery_deadline);
        const created = await api<Cargo>("/cargo", role, payload);
        createdCargo = created;
        if (extraction?.document_id)
          await api(
            `/cargo/${created.id}/documents/${extraction.document_id}`,
            role,
            {},
          );
      } else {
        const vessel = data.vessels.find((v: Data) => v.id === vesselId);
        await api("/availability", role, {
          vessel_id: vesselId,
          origin: fields.origin,
          destination: fields.destination,
          available_from: isoTime(fields.available_from),
          available_until: isoTime(fields.available_until),
          capacity_tonnes: Number(fields.capacity_tonnes),
          volume_m3: vessel.max_volume_m3,
        });
      }
      await done(createdCargo);
    } catch (e) {
      setError(
        (e as Error).message === "Invalid time value"
          ? "Confirm all required dates and times."
          : (e as Error).message,
      );
    } finally {
      setBusy(false);
    }
  }
  async function toggleRecording() {
    if (recording) {
      recorder.current?.stop();
      setRecording(false);
      return;
    }
    setError("");
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Recording requires localhost or HTTPS. Upload audio or type a transcript.",
        );
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      chunks.current = [];
      recorder.current = new MediaRecorder(stream.current);
      recorder.current.ondataavailable = (e) => chunks.current.push(e.data);
      recorder.current.onstop = () => {
        setFile(
          new File(chunks.current, "operator-recording.webm", {
            type: recorder.current?.mimeType || "audio/webm",
          }),
        );
        stream.current?.getTracks().forEach((t) => t.stop());
      };
      recorder.current.start();
      setRecording(true);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const required =
    kind === "cargo"
      ? [
          "cargo_type",
          "weight_tonnes",
          "packaging",
          "origin",
          "destination",
          "ready_time",
          "delivery_deadline",
        ]
      : [
          "capacity_tonnes",
          "origin",
          "destination",
          "available_from",
          "available_until",
        ];
  const missing = required.filter((k) => !fields[k]);
  function demoManual() {
    const cargo = data.cargo.find((c: Cargo) => c.id === "hero-cargo");
    if (!cargo) return;
    setFields((f) => ({
      ...f,
      ...Object.fromEntries(
        [
          "cargo_type",
          "weight_tonnes",
          "volume_m3",
          "packaging",
          "origin",
          "destination",
          "first_mile_required",
          "last_mile_required",
          "consolidation_allowed",
          "hazardous",
          "fragile",
          "perishable",
          "temperature_control_required",
        ].map((k) => [k, cargo[k]]),
      ),
      ready_time: inputTime(cargo.ready_time),
      delivery_deadline: inputTime(cargo.delivery_deadline),
    }));
  }
  return (
    <Panel
      title={
        kind === "cargo" ? "Create cargo request" : "Publish boat availability"
      }
      eyebrow="UNDERSTAND → REVIEW → CONFIRM"
      action={
        close && (
          <button aria-label="Close intake" onClick={close}>
            <X size={20} />
          </button>
        )
      }
    >
      <div className="form-content">
        <div className="tabs">
          {(kind === "cargo"
            ? ["text", "document", "manual", "bulk"]
            : ["voice", "manual"]
          ).map((t) => (
            <button
              className={tab === t ? "active" : ""}
              key={t}
              onClick={() => {
                setTab(t);
                setFile(null);
              }}
            >
              {t === "document" ? (
                <FileText size={15} />
              ) : t === "voice" ? (
                <Mic size={15} />
              ) : (
                <Keyboard size={15} />
              )}
              {
                {
                  text: "Describe cargo",
                  document: "Upload document",
                  manual: "Manual entry",
                  bulk: "Bulk CSV / XLSX",
                  voice: "Voice / transcript",
                }[t]
              }
            </button>
          ))}
        </div>
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        {tab === "text" || tab === "voice" ? (
          <>
            <label className="field">
              {kind === "cargo"
                ? "Cargo description"
                : "Malayalam or transliterated transcript"}
              <textarea
                rows={4}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </label>
            {kind === "vessel" && (
              <>
                <div className="shipment-actions">
                  <button className="button" onClick={toggleRecording}>
                    {recording ? <Square size={15} /> : <Mic size={15} />}{" "}
                    {recording ? "Stop recording" : "Record audio"}
                  </button>
                  <button className="button" onClick={() => parse(true)}>
                    Use demo transcript
                  </button>
                </div>
                <label className="upload-box">
                  <Upload size={23} />
                  Upload operator audio
                  <input
                    aria-label="Operator audio"
                    type="file"
                    accept="audio/*,.webm"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={useDemo}
                    onChange={(e) => setUseDemo(e.target.checked)}
                  />
                  Use the disclosed demo transcript if live STT fails
                </label>
                {file && <small>Selected: {file.name}</small>}
              </>
            )}
            <div className="form-actions">
              <button
                className="button primary"
                disabled={busy || recording}
                onClick={() => parse()}
              >
                {busy ? "Extracting…" : "Extract & review"}
              </button>
            </div>
            <p className="provenance-mini">
              Without credentials, a deterministic parser runs locally. Demo
              audio fallback uses a sample transcript and does not transcribe
              your recording.
            </p>
          </>
        ) : null}
        {(tab === "document" || tab === "bulk") && (
          <>
            <label className="upload-box">
              <FileText size={28} />
              <strong>
                {tab === "bulk"
                  ? "Bulk spreadsheet preview"
                  : "Purchase order, invoice or BOQ"}
              </strong>
              <small>
                {tab === "bulk"
                  ? "CSV or XLSX · 200 rows · timezone-aware dates"
                  : "Text or scanned PDF, TXT, PNG or JPEG · max 8 MB"}
              </small>
              <input
                aria-label="Cargo document"
                type="file"
                accept={
                  tab === "bulk"
                    ? ".csv,.xlsx"
                    : ".pdf,.txt,.csv,.png,.jpg,.jpeg"
                }
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
            <button
              className="button primary"
              disabled={busy}
              onClick={() => parse()}
            >
              {busy
                ? "Reading…"
                : tab === "bulk"
                  ? "Validate spreadsheet"
                  : "Extract document"}
            </button>
            {tab === "bulk" && (
              <button
                className="button"
                onClick={() =>
                  download(
                    "/intake/cargo/bulk-template",
                    role,
                    "jalayatra-cargo-template.xlsx",
                  ).catch((e) => setError(e.message))
                }
              >
                Download XLSX template
              </button>
            )}
          </>
        )}
        {bulk && (
          <div className="intake-review">
            <h3>Bulk preview · {bulk.rows.length} rows</h3>
            {bulk.rows.map((r: Data) => (
              <div className="report-card" key={r.row}>
                Row {r.row}: <Badge value={r.valid ? "PASS" : "FAIL"} />
                {r.valid && (
                  <p>
                    {r.reference || "No reference"} · {r.fields.cargo_type} ·{" "}
                    {r.fields.weight_tonnes} t · {r.fields.origin} →{" "}
                    {r.fields.destination}
                  </p>
                )}
                {r.warnings.map((warning: string) => (
                  <small key={warning}>{warning}</small>
                ))}
                {!r.valid && (
                  <small>{r.errors.map((e: Data) => e.msg).join("; ")}</small>
                )}
              </div>
            ))}
            <button
              className="button primary"
              disabled={busy || !bulk.valid_count}
              onClick={async () => {
                setBusy(true);
                try {
                  await api(
                    `/intake/cargo/bulk-import/${bulk.preview_id}?approved=true`,
                    role,
                    {},
                  );
                  await done();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              Import {bulk.valid_count} valid rows only
            </button>
            <button
              className="button"
              onClick={() =>
                download(
                  `/intake/cargo/bulk-preview/${bulk.preview_id}/errors`,
                  role,
                  "import-errors.csv",
                ).catch((e) => setError(e.message))
              }
            >
              Download error report
            </button>
            <button className="button" onClick={() => setBulk(null)}>
              Cancel import
            </button>
          </div>
        )}
        {(extraction || tab === "manual") && (
          <div className="intake-review">
            <div className="section-heading">
              <h3>Check the details before saving</h3>
              {kind === "cargo" && tab === "manual" && (
                <button className="text-button" onClick={demoManual}>
                  Fill demo cargo
                </button>
              )}
            </div>
            {extraction && (
              <>
                <div className="alert">
                  <Check size={16} />
                  {extraction.source === "llm"
                    ? "Configured AI extraction"
                    : "Details filled from your description"}{" "}
                  · confirm every field
                </div>
                {extraction.transcript && (
                  <p className="role-intro">
                    <Badge
                      value={
                        extraction.transcription_source === "configured_stt"
                          ? "LIVE SPEECH"
                          : extraction.transcription_source.includes("demo")
                            ? "DEMO TRANSCRIPT FALLBACK"
                            : "TYPED TRANSCRIPT"
                      }
                    />
                    Transcript: “{extraction.transcript}”
                    <small>{extraction.transcription_source}</small>
                  </p>
                )}
                {extraction.warnings.map((w: string) => (
                  <div className="alert" key={w}>
                    {w}
                  </div>
                ))}
                {extraction.document_recognition && (
                  <p className="provenance-mini">
                    Document recognition:{" "}
                    {extraction.document_recognition.source} · recognition
                    confidence{" "}
                    {extraction.document_recognition.confidence ??
                      "unavailable"}
                  </p>
                )}
                <p className="provenance-mini">
                  Extraction review:{" "}
                  {extraction.is_ai
                    ? "provider-supplied values require confirmation"
                    : "local rules identified explicit fields"}
                  . Extraction confidence is heuristic and is not measured model
                  accuracy. Missing or uncertain information requires manual
                  review.
                </p>
                {extraction.document_details && (
                  <div className="cost-details">
                    {Object.entries(extraction.document_details)
                      .filter(([, value]) => value !== null)
                      .map(([key, value]) => (
                        <div key={key}>
                          <span>{key.replaceAll("_", " ")}</span>
                          <strong>{String(value)}</strong>
                        </div>
                      ))}
                  </div>
                )}
                {extraction.missing_fields.length > 0 && (
                  <p className="provenance-mini">
                    Missing from input: {extraction.missing_fields.join(", ")}.
                    Fill and confirm below.
                  </p>
                )}
              </>
            )}
            {kind === "vessel" && (
              <label className="field">
                Registered vessel
                <select
                  value={vesselId}
                  onChange={(e) => setVesselId(e.target.value)}
                >
                  {data.vessels.map((v: Data) => (
                    <option key={v.id} value={v.id}>
                      {v.name} · {v.max_capacity_tonnes} t
                    </option>
                  ))}
                </select>
                <small>
                  Physical dimensions and certificates come from this profile.
                  Prefilled availability times are demo suggestions to confirm.
                </small>
              </label>
            )}
            <div className="form-grid">
              {(kind === "cargo"
                ? [
                    "cargo_type",
                    "weight_tonnes",
                    "volume_m3",
                    "packaging",
                    "origin",
                    "destination",
                    "ready_time",
                    "delivery_deadline",
                  ]
                : [
                    "capacity_tonnes",
                    "origin",
                    "destination",
                    "available_from",
                    "available_until",
                  ]
              ).map((key) => (
                <label key={key} className="field">
                  {(
                    {
                      cargo_type: "Goods to transport",
                      weight_tonnes: "Weight (tonnes)",
                      volume_m3: "Volume (m³)",
                      packaging: "Packaging",
                      origin: "Pickup location",
                      destination: "Delivery location",
                      ready_time: "Ready for pickup",
                      delivery_deadline: "Deliver by",
                      capacity_tonnes: "Available capacity (tonnes)",
                      available_from: "Available from",
                      available_until: "Available until",
                    } as Record<string, string>
                  )[key] || key.replace(/_/g, " ")}{" "}
                  {required.includes(key) && "*"}
                  {["origin", "destination"].includes(key) ? (
                    <select
                      aria-label={key}
                      value={fields[key]}
                      onChange={(e) => update(key, e.target.value)}
                    >
                      <option value="">Select location</option>
                      {places.map((p) => (
                        <option key={p}>{p}</option>
                      ))}
                    </select>
                  ) : key === "cargo_type" ? (
                    <select
                      aria-label={key}
                      value={fields[key]}
                      onChange={(e) => update(key, e.target.value)}
                    >
                      <option value="">Select cargo</option>
                      {[
                        "cement",
                        "steel",
                        "construction",
                        "coir",
                        "rice",
                        "general",
                      ].map((c) => (
                        <option key={c}>{c}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      aria-label={key}
                      type={
                        key.includes("tonnes") || key === "volume_m3"
                          ? "number"
                          : key.endsWith("_time") ||
                              key.endsWith("_deadline") ||
                              key.startsWith("available_")
                            ? "datetime-local"
                            : "text"
                      }
                      min="0.01"
                      step="any"
                      value={fields[key]}
                      onChange={(e) => update(key, e.target.value)}
                    />
                  )}{" "}
                  {extraction?.confidence[key] && (
                    <small className="confidence">
                      Extraction confidence{" "}
                      {Math.round(extraction.confidence[key] * 100)}% ·
                      heuristic, not calibrated accuracy
                    </small>
                  )}
                </label>
              ))}
            </div>
            {kind === "cargo" &&
              [
                "first_mile_required",
                "last_mile_required",
                "consolidation_allowed",
                "hazardous",
                "fragile",
                "perishable",
                "temperature_control_required",
              ].map((key) => (
                <label className="checkbox" key={key}>
                  <input
                    type="checkbox"
                    checked={!!fields[key]}
                    onChange={(e) => update(key, e.target.checked)}
                  />
                  {key.replace(/_/g, " ")}
                </label>
              ))}
            {missing.length > 0 && (
              <small>Complete: {missing.join(", ")}</small>
            )}
            <div className="form-actions">
              {close && (
                <button className="button" onClick={close}>
                  Cancel
                </button>
              )}
              <button
                className="button primary"
                disabled={busy || missing.length > 0}
                onClick={save}
              >
                {busy
                  ? "Saving…"
                  : kind === "cargo"
                    ? "Confirm & create cargo"
                    : "Confirm availability & find cargo"}
              </button>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
