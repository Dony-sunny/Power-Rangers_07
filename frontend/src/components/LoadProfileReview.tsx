import { useEffect, useState } from "react";
import { api, type Act, type Data, date } from "../api";
import { Panel } from "./UI";

const numericFields: [string, string][] = [["heaviest_piece_tonnes", "Heaviest piece (t)"], ["pieces", "Number of pieces"], ["unit_length_m", "Maximum piece length (m)"], ["unit_width_m", "Maximum piece width (m)"], ["unit_height_m", "Maximum piece height (m)"]];
export default function LoadProfileReview({ cargoId, role, act, busy }: { cargoId: string; role: string; act: Act; busy: boolean }) {
  const [fields, setFields] = useState<Data>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reviewed, setReviewed] = useState(false);
  useEffect(() => {
    let active = true;
    setFields({}); setReviewed(false); setError(""); setLoading(true);
    api(`/lines/cargo/${cargoId}/profile`, role).then((result) => active && setFields(result.profile || {})).catch((e) => active && setError(e.message)).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [cargoId, role]);
  return <Panel title="Review imported load units" eyebrow="REQUIRED BEFORE A DATED QUOTE">
    <p className="role-intro">Confirm the piece count, maximum unit dimensions and heaviest individual piece from the cargo documents. These values determine truck trips and compatible handling equipment.</p>
    {error && <p role="alert">{error}</p>}
    <div className="form-content"><div className="form-grid">{numericFields.map(([key, label]) => <label className="field" key={key}>{label}<input type="number" min={key === "pieces" ? 1 : 0.001} step={key === "pieces" ? 1 : "any"} value={fields[key] ?? ""} disabled={loading || busy} onChange={(e) => { setReviewed(false); setFields((old) => ({ ...old, [key]: e.target.value === "" ? "" : Number(e.target.value) })); }} /></label>)}</div>
      {(fields.receiving_from || fields.receiving_until) && <p>Stored receiving window: {date(fields.receiving_from)} – {date(fields.receiving_until)}.</p>}
      <label className="checkbox"><input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} />I checked these load units against the cargo documents.</label>
      <button className="button primary" disabled={busy || loading || !reviewed || numericFields.some(([key]) => !Number.isFinite(fields[key]) || fields[key] <= 0)} onClick={() => act(() => api(`/lines/cargo/${cargoId}/profile`, role, Object.fromEntries([...numericFields.map(([key]) => [key, fields[key]]), ["receiving_from", fields.receiving_from || null], ["receiving_until", fields.receiving_until || null]])), "Reviewed load profile saved.")}>Save reviewed load units</button>
    </div>
  </Panel>;
}
