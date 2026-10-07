import { useEffect, useState } from "react";
import { api, type Data, type Act, title } from "../api";
import { Panel, Badge, Stat } from "./UI";

export function ProviderDiagnostics({
  role,
  act,
  busy,
}: {
  role: string;
  act: Act;
  busy: boolean;
}) {
  const [status, setStatus] = useState<Data | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/providers/diagnostics", role)
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, [role]);
  return (
    <Panel
      title="Provider diagnostics"
      eyebrow="CONNECTION STATUS · NO SECRETS"
    >
      {error && <div className="alert error">{error}</div>}
      <div className="stats-row">
        <Stat
          label="AI provider"
          value={status?.ai.status || "Checking"}
          note={
            status?.ai.configured
              ? "Configured; connection requires a valid response"
              : "No credential configured"
          }
        />
        <Stat
          label="Malayalam speech"
          value={status?.stt.status || "Checking"}
          note="Validate by uploading actual audio"
        />
        <Stat
          label="Demo fallback"
          value={status?.fallback.status || "Checking"}
          note="Deterministic, available offline"
        />
      </div>
      <button
        className="button"
        disabled={busy}
        onClick={() =>
          act(
            async () =>
              setStatus(await api("/providers/diagnostics", role, {})),
            "Provider diagnostic completed; unavailable services retain local fallback.",
          )
        }
      >
        Run AI connection check
      </button>
      {status?.connectors && (
        <div className="notice-list">
          <h3>Optional connector contracts</h3>
          <p>
            Tracking:{" "}
            {status.connectors.tracking.configured
              ? "configured; validate an authorized position request"
              : "simulated demo"}
            . Weather:{" "}
            {status.connectors.weather.configured
              ? "configured; validate a location request"
              : "simulated demo"}
            .
          </p>
          <p>
            Payments, insurance and government: Prototype / Not connected.
            Identity: signed stored users; enterprise SSO remains a production
            requirement.
          </p>
        </div>
      )}
      <p>
        Credentials are never returned. Speech status changes only after a
        successful transcription. No external provider has been
        credential-tested unless this instance records a successful request.
      </p>
    </Panel>
  );
}

export default function Administration({
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
  const [orgName, setOrgName] = useState(""),
    [kind, setKind] = useState("shipper"),
    [userName, setUserName] = useState(""),
    [orgId, setOrgId] = useState(data.organizations[0]?.id || ""),
    [roleId, setRoleId] = useState("shipper"),
    [roles, setRoles] = useState<Data>({});
  useEffect(() => {
    api("/health", role).then((r) => setRoles(r.roles));
  }, [role]);
  return (
    <>
      <ProviderDiagnostics role={role} act={act} busy={busy} />
      <Panel title="Organization and user administration">
        <div className="form-content">
          <h3>Create organization</h3>
          <div className="form-grid">
            <label className="field">
              Organization name
              <input
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            </label>
            <label className="field">
              Organization type
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                {[
                  "shipper",
                  "operator",
                  "logistics",
                  "terminal",
                  "authority",
                  "government",
                ].map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="button"
            disabled={busy || orgName.length < 2}
            onClick={() =>
              act(async () => {
                await api("/admin/organizations", role, {
                  name: orgName,
                  kind,
                  verified: false,
                });
                setOrgName("");
              }, "Organization created.")
            }
          >
            Create organization
          </button>
          <h3>Add an organization member</h3>
          <div className="form-grid">
            <label className="field">
              Member name
              <input
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </label>
            <label className="field">
              Organization
              <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                {data.organizations.map((o: Data) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Assigned role
              <select
                value={roleId}
                onChange={(e) => setRoleId(e.target.value)}
              >
                {Object.entries(roles).map(([key, label]) => (
                  <option key={key} value={key}>
                    {String(label)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="button primary"
            disabled={busy || userName.length < 2}
            onClick={() =>
              act(async () => {
                await api("/admin/users", role, {
                  name: userName,
                  organization_id: orgId,
                  role_id: roleId,
                });
                setUserName("");
              }, "Member created with database-backed role.")
            }
          >
            Create user
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Member</th>
                <th>Organization</th>
                <th>Role</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u: Data) => (
                <tr key={u.id}>
                  <td>
                    {u.name}
                    <small>{u.id}</small>
                  </td>
                  <td>
                    {
                      data.organizations.find(
                        (o: Data) => o.id === u.organization_id,
                      )?.name
                    }
                  </td>
                  <td>
                    <select
                      aria-label={`Role for ${u.name}`}
                      value={u.role_id}
                      disabled={busy || u.id === data.actor.id}
                      onChange={(e) =>
                        act(
                          () =>
                            api(
                              `/admin/users/${u.id}`,
                              role,
                              { role_id: e.target.value },
                              "PATCH",
                            ),
                          "Role updated; subsequent requests use the new permission.",
                        )
                      }
                    >
                      {Object.entries(roles).map(([key, label]) => (
                        <option key={key} value={key}>
                          {String(label)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <Badge value={u.disabled ? "DISABLED" : "ACTIVE"} />
                  </td>
                  <td>
                    <button
                      className="button small"
                      disabled={busy || u.id === data.actor.id}
                      onClick={() =>
                        act(
                          () =>
                            api(
                              `/admin/users/${u.id}`,
                              role,
                              { disabled: !u.disabled },
                              "PATCH",
                            ),
                          u.disabled
                            ? "User enabled."
                            : "User disabled; access revoked.",
                        )
                      }
                    >
                      {u.disabled ? "Enable user" : "Disable user"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
