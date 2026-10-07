import { useEffect, useState } from "react";
import { api, download, type Data, type Act, date, title } from "../api";
import { Panel, Badge, Empty } from "./UI";

export default function Evidence({
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
  const [selected, setSelected] = useState(
      data.shipments[0]?.shipment.id || "",
    ),
    [photos, setPhotos] = useState<Data[]>([]),
    [error, setError] = useState(""),
    [file, setFile] = useState<File | null>(null),
    [category, setCategory] = useState(
      role === "receiver" ? "POD" : "HANDOVER",
    ),
    [description, setDescription] = useState(""),
    [label, setLabel] = useState<Data | null>(null),
    [challenge, setChallenge] = useState<Data | null>(null),
    [code, setCode] = useState("");
  const item = data.shipments.find((s: Data) => s.shipment.id === selected);
  async function refresh() {
    if (!selected) return;
    try {
      const listed = await api(`/shipments/${selected}/photos`, role);
      setPhotos(
        await Promise.all(
          listed.photos.map((p: Data) => api(`/photos/${p.id}`, role)),
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    setLabel(null);
    setChallenge(null);
    refresh();
  }, [selected, role]);
  if (!data.shipments.length)
    return (
      <Panel title="Shipment evidence & labels">
        <Empty>
          Book a shipment to attach evidence, generate a QR label, or verify
          delivery.
        </Empty>
      </Panel>
    );
  return (
    <>
      <Panel
        title="Shipment evidence & authorized labels"
        eyebrow="AUDITABLE HANDOVER"
      >
        <div className="form-content">
          {error && <div className="alert error">{error}</div>}
          <label className="field">
            Assigned shipment
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {data.shipments.map((s: Data) => (
                <option key={s.shipment.id} value={s.shipment.id}>
                  {s.cargo.cargo_type} · {s.cargo.weight_tonnes} t ·{" "}
                  {s.shipment.id}
                </option>
              ))}
            </select>
          </label>
          <div className="shipment-actions">
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  async () =>
                    setLabel(await api(`/labels/shipment/${selected}`, role)),
                  "Authorized QR label generated.",
                )
              }
            >
              Generate shipment QR label
            </button>
            <button
              className="button"
              onClick={() =>
                act(
                  () =>
                    download(
                      `/labels/shipment/${selected}/print`,
                      role,
                      "jalayatra-shipment-label.html",
                    ),
                  "Printable label downloaded.",
                )
              }
            >
              Download printable label
            </button>
          </div>
          {label && (
            <div className="label-preview">
              <img
                alt="Shipment QR code"
                src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(label.qr_svg)}`}
                width="180"
              />
              <div>
                <h3>
                  {label.entity.cargo_type} · {label.entity.weight_tonnes} t
                </h3>
                <p>
                  {label.entity.origin} → {label.entity.destination}
                </p>
                <a href={label.payload}>Open authorized shipment reference</a>
                <small>
                  QR contains an opaque reference. Access still requires
                  authorization.
                </small>
              </div>
            </div>
          )}
          {[
            "warehouse",
            "receiver",
            "dispatch",
            "terminal",
            "captain",
            "control",
            "admin",
          ].includes(role) && (
            <>
              <h3>Add operational evidence</h3>
              <div className="form-grid">
                <label className="field">
                  Evidence category
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  >
                    {[
                      "LOADING",
                      "HANDOVER",
                      "DAMAGE",
                      "TERMINAL",
                      "DISCREPANCY",
                      "POD",
                      "NAVIGATION",
                    ].map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  Description
                  <input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </label>
                <label className="field">
                  Photo (PNG/JPEG, 2 MB)
                  <input
                    aria-label="Evidence photo"
                    type="file"
                    accept=".png,.jpg,.jpeg"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
              </div>
              <button
                className="button primary"
                disabled={busy || !file}
                onClick={() =>
                  act(async () => {
                    const form = new FormData();
                    form.append("file", file!);
                    form.append("category", category);
                    form.append("description", description);
                    await api(`/shipments/${selected}/photos`, role, form);
                    setFile(null);
                    await refresh();
                  }, "Evidence saved with uploader and timestamp.")
                }
              >
                Save photo evidence
              </button>
            </>
          )}
          <div className="evidence-grid">
            {photos.map((p) => (
              <figure key={p.id}>
                <img
                  src={p.data_url}
                  alt={p.description || title(p.category)}
                />
                <figcaption>
                  <strong>{title(p.category)}</strong>
                  <p>{p.description}</p>
                  <small>
                    {date(p.created_at)} · {p.uploader_id}
                  </small>
                </figcaption>
              </figure>
            ))}
          </div>
          {!photos.length && (
            <Empty>No photos attached to this shipment.</Empty>
          )}
        </div>
      </Panel>
      {role === "receiver" && item && (
        <Panel
          title="Receiver delivery verification"
          eyebrow="PROTOTYPE OTP · NOT A LEGAL DIGITAL SIGNATURE"
        >
          <div className="form-content">
            <Badge
              value={
                item.shipment.operational_data?.pod_verified
                  ? "VERIFIED_PASS"
                  : "UNVERIFIED"
              }
            />
            <p>
              At unloading or last mile, request a challenge. Once requested,
              delivery is blocked until this receiver verifies it.
              Milestone-only demo deliveries are unverified.
            </p>
            <button
              className="button primary"
              disabled={
                busy ||
                !["UNLOADING", "LAST_MILE"].includes(item.shipment.status)
              }
              onClick={() =>
                act(async () => {
                  const issued = await api(
                    `/shipments/${selected}/delivery-challenge`,
                    role,
                    {},
                  );
                  setChallenge(issued);
                  setCode("");
                }, "Local prototype verification challenge issued.")
              }
            >
              Request delivery OTP
            </button>
            {challenge && (
              <>
                <p>
                  {challenge.provider} · Expires {date(challenge.expires_at)}
                </p>
                <div className="alert">
                  Demo receiver code: <strong>{challenge.demo_otp}</strong>
                </div>
                <label className="field">
                  Enter delivery OTP
                  <input
                    aria-label="Delivery OTP"
                    inputMode="numeric"
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                </label>
                <button
                  className="button primary"
                  disabled={busy || code.length !== 6}
                  onClick={() =>
                    act(async () => {
                      await api(
                        `/delivery-challenges/${challenge.challenge_id}/verify`,
                        role,
                        { code },
                      );
                      setChallenge(null);
                    }, "Receiver identity and delivery OTP verified.")
                  }
                >
                  Verify delivery OTP
                </button>
              </>
            )}
          </div>
        </Panel>
      )}
    </>
  );
}
