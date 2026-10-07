import { Check, ArrowRight, Download, FileCheck2 } from "lucide-react";
import coverage from "../challenge-coverage.json";
import { Panel } from "./UI";

export default function ChallengeCoverage({
  role,
  setView,
  switchRole,
}: {
  switchRole?: (role: string) => void;
  role: string;
  setView: (view: string) => void;
}) {
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(coverage, null, 2)], {
        type: "application/json",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "Jalayatra-challenge-coverage.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <div className="cargo-lines challenge-coverage">
      <div className="journey-intro">
        <FileCheck2 size={28} />
        <div>
          <h2>Every brief feature, one connected delivery.</h2>
          <p>
            {coverage.challenge} · {coverage.event}
          </p>
          <p>
            Construction materials from Kochi to Alappuzha: post cargo, find an
            available boat, compare the full cost and plan the delivery.
          </p>
        </div>
      </div>
      <div className="line-note">
        <strong>Local demonstration</strong>
        <p>{coverage.prototype_status}</p>
        <button className="button small" onClick={download}>
          <Download size={15} /> Download coverage evidence
        </button>
      </div>
      <div className="coverage-grid">
        {coverage.requirements.map((feature, index) => (
          <Panel
            key={feature.id}
            title={feature.name}
            eyebrow={index < 5 ? `BRIEF FEATURE ${index + 1}` : "STATED IMPACT"}
          >
            <p className="coverage-status">
              <Check size={17} /> Implemented in the local prototype
            </p>
            <p>{feature.behavior}</p>
            <div className="line-note">
              <strong>See it work</strong>
              <p>{feature.demo}</p>
            </div>
            {feature.workspace === role ? (
              <button
                className="button small"
                onClick={() => setView(feature.view)}
              >
                Open this workflow <ArrowRight size={15} />
              </button>
            ) : switchRole ? (
              <button
                className="button small"
                onClick={() => switchRole(feature.workspace)}
              >
                Open{" "}
                {feature.workspace === "operator"
                  ? "boat operator"
                  : feature.workspace === "control"
                    ? "logistics coordinator"
                    : "cargo owner"}{" "}
                workspace <ArrowRight size={15} />
              </button>
            ) : (
              <p className="muted">
                Workspace:{" "}
                {feature.workspace === "operator"
                  ? "Boat operator"
                  : feature.workspace === "control"
                    ? "Logistics coordinator"
                    : "Cargo owner / shipper"}
              </p>
            )}
            <details>
              <summary>Source, API and verification scenarios</summary>
              <ul>
                {feature.api.map((item) => (
                  <li key={item}>
                    <code>{item}</code>
                  </li>
                ))}
              </ul>
              <p className="muted">Repository source</p>
              {feature.source_files.map((item) => (
                <code className="evidence-path" key={item}>
                  {item}
                </code>
              ))}
              <p className="muted">
                Verification scenarios (run these to verify)
              </p>
              {feature.test_files.map((item) => (
                <code className="evidence-path" key={item}>
                  {item}
                </code>
              ))}
            </details>
          </Panel>
        ))}
      </div>
      <Panel title="Four target user groups, three main workspaces">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Target user from the brief</th>
                <th>Where they participate</th>
              </tr>
            </thead>
            <tbody>
              {coverage.target_users.map((user) => (
                <tr key={user.name}>
                  <td>{user.name}</td>
                  <td>{user.workspace}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <Panel title="What the demonstration measures">
        <p>
          Selected and completed water tonnes show waterway use. Full delivery
          CO₂ estimates include connecting trucks; modeled sailing contribution
          shows the operator’s commercial incentive.
        </p>
        <ul>
          {coverage.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
