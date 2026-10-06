import { useState, useEffect, useCallback } from "react";
import {
  Anchor,
  ChevronDown,
  LayoutDashboard,
  Package,
  Radio,
  CalendarDays,
  Settings2,
  Menu,
  Plus,
  ArrowUpRight,
  RefreshCw,
  X,
  Check,
} from "lucide-react";
import { api, type Data, type Cargo, type Act, date, title } from "./api";
import RouteMap from "./components/RouteMap";
import { Panel, Empty, Loading, Badge, TerminalTable } from "./components/UI";
import Planner from "./components/Planner";
import Intake from "./components/Intake";
import Workspaces from "./components/Workspaces";

export const roles: Record<string, string> = {
  shipper: "Shipper procurement",
  dispatch: "Shipper dispatch",
  warehouse: "Warehouse",
  receiver: "Consignee",
  operator: "Vessel operator",
  fleet: "Fleet dispatcher",
  captain: "Captain",
  terminal: "Terminal operator",
  control: "3PL control tower",
  finance: "Finance",
  compliance: "Compliance & safety",
  maintenance: "Maintenance",
  network: "Waterway control",
  government: "Government analytics",
  admin: "Platform admin",
};
const intros: Record<string, [string, string]> = {
  shipper: [
    "A smarter way to move freight.",
    "Plan, compare and book your next journey along Kerala’s waterways.",
  ],
  operator: [
    "Make every voyage count.",
    "Turn available capacity into cargo, and empty returns into opportunity.",
  ],
  control: [
    "Your network, in one view.",
    "Coordinate freight, resolve exceptions and keep cargo moving.",
  ],
  government: [
    "Better waterways. Measurable impact.",
    "Turn freight transactions into transparent network intelligence.",
  ],
  captain: [
    "Ready for your next voyage.",
    "Your manifest, approved route and voyage milestones.",
  ],
  dispatch: [
    "From booking to delivery.",
    "Coordinate handovers, terminals and shipment exceptions.",
  ],
  warehouse: [
    "Prepare the next load.",
    "Verify cargo readiness and complete the loading handover.",
  ],
  receiver: [
    "Know what’s arriving.",
    "Track incoming cargo and record delivery acceptance.",
  ],
  fleet: [
    "Keep your fleet moving.",
    "Manage availability, assignments and vessel conflicts.",
  ],
  terminal: [
    "An organized waterfront.",
    "Coordinate berth windows, vessel arrivals and equipment.",
  ],
  finance: [
    "Every charge, accounted for.",
    "Review invoices, payment states and operator settlements.",
  ],
  compliance: [
    "Safety before sailing.",
    "Review certificates, cargo compatibility and the audit trail.",
  ],
  maintenance: [
    "A reliable fleet starts here.",
    "Report defects and manage vessel return to service.",
  ],
  network: [
    "A clearer view of the waterway.",
    "Monitor restrictions, terminals and navigation reports.",
  ],
  admin: [
    "Keep the exchange in good order.",
    "Manage the demo, identities, providers and platform trust.",
  ],
};

export default function App() {
  const [role, setRole] = useState(() => {
      const saved = localStorage.getItem("jalayatra-role");
      return saved && saved in roles ? saved : "shipper";
    }),
    [view, setView] = useState("overview"),
    [data, setData] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [showIntake, setShowIntake] = useState(false),
    [mobileMenu, setMobileMenu] = useState(false);
  const load = useCallback(async () => {
    try {
      const snapshot = await api("/workspace", role);
      setData(snapshot);
      setError("");
      if (role === "captain")
        localStorage.setItem(
          "jalayatra-captain-cache",
          JSON.stringify({ snapshot, stored_at: new Date().toISOString() }),
        );
    } catch (e) {
      const cache =
        role === "captain"
          ? localStorage.getItem("jalayatra-captain-cache")
          : null;
      if (cache) {
        try {
          const saved = JSON.parse(cache);
          setData({ ...saved.snapshot, offline: true });
          setNotice(
            `Offline cached voyage view from ${date(saved.stored_at)}. Reconnect before confirming milestones.`,
          );
          setError("");
        } catch {
          setError((e as Error).message);
        }
      } else setError((e as Error).message);
    }
  }, [role]);
  useEffect(() => {
    setData(null);
    setView("overview");
    load();
    localStorage.setItem("jalayatra-role", role);
  }, [role, load]);
  const act: Act = async (task, message = "Saved successfully.") => {
    if (data?.offline) {
      setError("Reconnect to the local API before changing voyage records.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await task();
      setNotice(message);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const isPlanner = ["shipper", "control"].includes(role);
  const nav =
    role === "shipper"
      ? ["overview", "cargo", "tracking", "services"]
      : role === "control"
        ? ["overview", "planner", "tracking", "services"]
        : role === "operator"
          ? ["overview", "voice", "fleet", "tracking"]
          : role === "government"
            ? ["overview", "network", "intelligence"]
            : role === "captain"
              ? ["overview", "tracking", "reports"]
              : role === "admin"
                ? ["overview", "demo", "audit"]
                : [
                    "overview",
                    "tracking",
                    ...(["network", "compliance"].includes(role)
                      ? ["network", "audit", "reports"]
                      : []),
                  ];
  const navLabels: Record<string, string> = {
    overview:
      role === "shipper"
        ? "Transport planner"
        : role === "government"
          ? "Impact overview"
          : "Workspace",
    planner: "Multimodal planning",
    cargo: "Cargo requests",
    tracking: "Shipments & tracking",
    services: "Scheduled services",
    voice: "Voice availability",
    fleet: "Vessels & availability",
    network: "Waterway network",
    intelligence: "Demand intelligence",
    demo: "Demo scenarios",
    audit: "Audit & trust",
    reports: "Navigation reports",
  };
  const [heading, subtitle] = intros[role] || intros.shipper;
  return (
    <div className={`app ${role === "captain" ? "captain" : ""}`}>
      <aside className={`sidebar ${mobileMenu ? "open" : ""}`}>
        <a className="brand" href="#" onClick={(e) => e.preventDefault()}>
          <span className="brand-mark">
            <Anchor size={24} />
          </span>
          <span>
            jalayatra<span className="brand-ai">AI</span>
            <small>INLAND FREIGHT EXCHANGE</small>
          </span>
        </a>
        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav>
          {nav.map((item, i) => {
            const Icon =
              [LayoutDashboard, Package, Radio, CalendarDays][i] || Radio;
            return (
              <button
                key={item}
                className={view === item ? "active" : ""}
                onClick={() => {
                  setView(item);
                  setMobileMenu(false);
                }}
              >
                <Icon size={19} />
                {navLabels[item]}
                {view === item && <span className="nav-dot" />}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="corridor-card">
            <Anchor size={22} />
            <strong>The NW-3 advantage</strong>
            <p>Connecting Kerala’s cargo with its waterways.</p>
            <span>
              KOCHI → ALAPPUZHA
              <ArrowUpRight size={14} />
            </span>
          </div>
          <button
            className="sidebar-link"
            onClick={() => {
              setRole("admin");
              setView("demo");
            }}
          >
            <Settings2 size={18} />
            Demo & settings
          </button>
          <div className="identity">
            <span className="avatar">{role === "shipper" ? "MB" : "JA"}</span>
            <div>
              <strong>{data?.organization?.name || "Jalayatra demo"}</strong>
              <small>{roles[role]}</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-toggle"
              aria-label="Open navigation"
              onClick={() => setMobileMenu(!mobileMenu)}
            >
              <Menu size={22} />
            </button>
            <span>Workspace</span>
            <span>/</span>
            <strong>{navLabels[view]}</strong>
          </div>
          <div className="topbar-actions">
            <span className="demo-indicator">
              <i />
              Demo network
            </span>
            <label className="role-select">
              <span className="sr-only">Demo role</span>
              <select
                aria-label="Demo role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                {Object.entries(roles).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} />
            </label>
            <button
              className="icon-button"
              aria-label="Refresh workspace"
              onClick={load}
            >
              <RefreshCw size={17} />
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="tiny-line" />
                KERALA’S FREIGHT OPERATING SYSTEM
              </div>
              <h1>{view === "overview" ? heading : navLabels[view]}</h1>
              <p>{subtitle}</p>
            </div>
            {isPlanner && (
              <button
                className="button primary"
                onClick={() => setShowIntake(true)}
              >
                <Plus size={17} />
                New cargo request
              </button>
            )}
          </div>
          {error && (
            <div className="alert error" role="alert">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="alert" role="status">
              <Check size={17} />
              {notice}
              <button
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {!data ? (
            <Loading />
          ) : view === "cargo" ? (
            <Panel title="Your cargo requests">
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Cargo</th>
                      <th>Route</th>
                      <th>Weight</th>
                      <th>Deadline</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.cargo.map((c: Cargo) => (
                      <tr key={c.id}>
                        <td>
                          <strong>{title(c.cargo_type)}</strong>
                          <small>{c.id}</small>
                        </td>
                        <td>
                          {c.origin} → {c.destination}
                        </td>
                        <td>{c.weight_tonnes} t</td>
                        <td>{date(c.delivery_deadline)}</td>
                        <td>
                          <Badge value={c.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          ) : view === "network" ? (
            <Panel title="NW-3 operational network">
              <RouteMap data={data} heat />
              <TerminalTable data={data} />
            </Panel>
          ) : (role === "shipper" && view === "overview") ||
            (role === "control" && view === "planner") ? (
            <Planner
              data={data}
              role={role}
              act={act}
              busy={busy}
              onBooked={() => setView("tracking")}
            />
          ) : (
            <RoleWorkspace
              data={data}
              role={role}
              view={view}
              act={act}
              busy={busy}
              setView={setView}
            />
          )}
          <footer>
            <span>
              <Anchor size={13} />
              Jalayatra AI
            </span>
            <span>
              Demonstration data · No live navigation or certified carbon claims
            </span>
            <span>Built for Kerala’s waterways</span>
          </footer>
        </main>
      </div>
      {showIntake && data && (
        <div className="modal-backdrop">
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Create cargo request"
          >
            <CargoIntake
              data={data}
              role={role}
              close={() => setShowIntake(false)}
              done={async () => {
                await load();
                setShowIntake(false);
                setView("cargo");
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
function RoleWorkspace(props: Data) {
  return (
    <Workspaces
      data={props.data}
      role={props.role}
      view={props.view}
      act={props.act}
      busy={props.busy}
      setView={props.setView}
    />
  );
}
function CargoIntake({ data, role, close, done }: Data) {
  return <Intake data={data} role={role} close={close} done={done} />;
}
