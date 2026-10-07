import { useEffect, useRef, useState } from "react";
import { api, type Act, type Data } from "../api";
import { workspaceGroups } from "../workspaceGroups";
import { Empty, Loading, Panel } from "./UI";
import Workspaces from "./Workspaces";
import Intake from "./Intake";
import { TruckAppointments } from "./OperationalTasks";
import TeamDelivery from "./TeamDelivery";
import FreightPlanning from "./FreightPlanning";
import PublicContext from "./PublicContext";

export default function TeamWorkspace({
  data,
  group,
  act,
  busy,
  openPlanner,
}: {
  data: Data;
  group: string;
  act: Act;
  busy: boolean;
  openPlanner: (cargo: string) => void;
}) {
  const teams = workspaceGroups[group];
  const [role, setRole] = useState(
    data.demo_mode ? teams[0].id : data.actor.role_id,
  );
  const team = teams.find((item) => item.id === role)!;
  const [view, setView] = useState(team.tools[0].id);
  const [snapshot, setSnapshot] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const context = useRef(role);
  context.current = role;
  useEffect(() => {
    let active = true;
    setSnapshot(null);
    setError("");
    api("/workspace", role)
      .then((result) => {
        if (active) setSnapshot(result);
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [role, data]);
  const teamAct: Act = (task, message) =>
    act(async () => {
      await task();
      const result = await api("/workspace", role);
      if (context.current === role) setSnapshot(result);
    }, message);
  const tools = [
    ...team.tools,
    { id: "context", label: "Route information & weather" },
  ];
  const props = { data: snapshot!, role, view, act: teamAct, busy, setView };
  return (
    <>
      <Panel
        title="Team tools"
        eyebrow={
          group === "shipper"
            ? "CARGO OWNER / SELLER"
            : group === "operator"
              ? "BOAT OPERATOR"
              : "LOGISTICS COORDINATOR"
        }
      >
        <div className="form-content">
          <label className="field">
            Team role
            <select
              aria-label="Team role"
              value={role}
              disabled={!data.demo_mode || busy}
              onChange={(e) => {
                const next = teams.find((item) => item.id === e.target.value)!;
                setRole(next.id);
                setView(next.tools[0].id);
              }}
            >
              {teams.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Tool
            <select
              aria-label="Team tool"
              value={
                tools.some((item) => item.id === view) ? view : tools[0].id
              }
              onChange={(e) => setView(e.target.value)}
            >
              {tools.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="role-intro">
          {team.description}{" "}
          {snapshot && (
            <>
              Organization:{" "}
              <strong>
                {snapshot.organization?.name || snapshot.actor.organization_id}
              </strong>
              .
            </>
          )}
          {data.demo_mode && (
            <>
              {" "}
              Role switching uses stored demo identities. Transactions and
              partner responses are simulated.
            </>
          )}
        </p>
      </Panel>
      {error ? (
        <Empty>
          <p role="alert">{error}</p>
          <button
            className="button"
            onClick={() =>
              teamAct(async () => setError(""), "Workspace refreshed.")
            }
          >
            Retry
          </button>
        </Empty>
      ) : !snapshot ? (
        <Loading />
      ) : view === "context" ? (
        <PublicContext role={role} />
      ) : view === "intake" ? (
        <Intake
          data={snapshot}
          role={role}
          done={() =>
            teamAct(
              async () => {},
              "Cargo imported. Review its load profile before requesting a quote.",
            )
          }
        />
      ) : view === "matching" ? (
        <FreightPlanning
          data={snapshot}
          role={role}
          act={teamAct}
          busy={busy}
          openPlanner={openPlanner}
        />
      ) : view === "appointments" ? (
        <TruckAppointments {...props} />
      ) : (
        <>
          {(view === "tracking" ||
            (role === "receiver" && view === "overview")) && (
            <TeamDelivery {...props} />
          )}
          <Workspaces {...props} />
        </>
      )}
    </>
  );
}
