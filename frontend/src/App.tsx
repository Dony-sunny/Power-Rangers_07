import { useCallback, useEffect, useRef, useState } from "react";
import {
  Anchor,
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Leaf,
  MapPin,
  Package,
  Plus,
  Search,
  ShoppingBag,
  X,
} from "lucide-react";
import { api, date, title, type Act, type Cargo, type Data } from "./api";
import { Badge, Empty, Loading } from "./components/UI";
import CargoLines from "./components/CargoLines";
import ChallengeCoverage from "./components/ChallengeCoverage";
import AvailabilityPosting from "./components/AvailabilityPosting";
import OperatorMarketplace from "./components/OperatorMarketplace";
import Marketplace from "./components/Marketplace";
import Posting from "./components/Posting";
import LogisticsMarketplace from "./components/LogisticsMarketplace";
import BoatRegistration from "./components/BoatRegistration";

export const roles: Record<string, string> = {
  shipper: "Cargo owner",
  operator: "Boat operator",
  control: "Logistics coordinator",
};
const pageLabels: Record<string, string> = {
  overview: "Browse boats",
  cargo: "My cargo",
  posting: "Post cargo",
  voice: "List your boat",
  fleet: "My boats",
  tracking: "My bookings",
  planner: "Plan a delivery",
  demand: "Find cargo",
  providers: "Provider jobs",
  coverage: "Challenge coverage",
};

export default function App() {
  const [role, setRole] = useState(() => {
    const saved = localStorage.getItem("jalayatra-role");
    return saved && roles[saved] ? saved : "shipper";
  });
  const [view, setView] = useState("overview");
  const [data, setData] = useState<Data | null>(null);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [cargoId, setCargoId] = useState("");
  const [vesselId, setVesselId] = useState("");
  const [availabilityId, setAvailabilityId] = useState("");
  const [editingListing, setEditingListing] = useState("");
  const [operatorUser, setOperatorUser] = useState(
    () => localStorage.getItem("jalayatra-operator-user") || "demo-operator",
  );
  const activeContext = useRef("");
  activeContext.current = `${role}:${operatorUser}`;
  const load = useCallback(async () => {
    const snapshot = await api("/workspace", role);
    if (activeContext.current !== `${role}:${operatorUser}`) return;
    setData(snapshot);
    if (!snapshot.demo_mode && snapshot.actor.role_id !== role)
      setRole(snapshot.actor.role_id);
  }, [role, operatorUser]);
  useEffect(() => {
    setData(null);
    localStorage.setItem("jalayatra-role", role);
    load().catch((e) => setError(e.message));
  }, [load, role]);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [view]);
  const navigate = (next: string) => {
    setView(next);
    setError("");
  };
  function switchRole(next: string, boatId?: string) {
    if (next === "operator" && boatId && data?.demo_mode) {
      const boat = data.vessels.find((v: Data) => v.id === boatId);
      const account =
        boat?.organization_id === "other-operator"
          ? "demo-pamba-operator"
          : "demo-operator";
      localStorage.setItem("jalayatra-operator-user", account);
      setOperatorUser(account);
    }
    setSearch("");
    setQuery("");
    setRole(next);
    setView(next === "shipper" ? "tracking" : "overview");
    setNotice("");
    setError("");
  }
  const act: Act = async (task, message = "Saved successfully.") => {
    setBusy(true);
    setError("");
    try {
      await task();
      await load();
      setNotice(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  function book(cargo: string, vessel: string, listing?: string) {
    setCargoId(cargo);
    setVesselId(vessel);
    setAvailabilityId(listing || "");
    navigate("planner");
  }
  function listBoat(boat = "") {
    setVesselId(boat);
    setSearch("");
    setQuery("");
    setEditingListing("");
    navigate("voice");
  }
  function editListing(listing: string, boat: string) {
    setEditingListing(listing);
    setVesselId(boat);
    navigate("voice");
  }
  const nav =
    role === "shipper"
      ? ["overview", "cargo", "tracking", "coverage"]
      : role === "operator"
        ? ["overview", "demand", "fleet", "voice", "tracking", "coverage"]
        : ["overview", "providers", "planner", "tracking", "coverage"];
  const ready =
    data &&
    data.actor.role_id === role &&
    (role !== "operator" || !data.demo_mode || data.actor.id === operatorUser);
  return (
    <div className="market-app">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="market-header">
        <button
          className="market-brand"
          onClick={() => navigate("overview")}
          aria-label="Jalayatra home"
        >
          <Anchor size={30} />
          <span>
            jalayatra<small>BACKWATER CARGO EXCHANGE</small>
          </span>
        </button>
        <div className="market-location">
          <MapPin size={19} />
          <span>
            Transport across<strong>Kerala waterways</strong>
          </span>
        </div>
        <form
          className="market-search"
          onSubmit={(e) => {
            e.preventDefault();
            setSearch(query);
            navigate(
              role === "operator"
                ? view === "fleet"
                  ? "fleet"
                  : "demand"
                : "overview",
            );
          }}
        >
          <label className="sr-only" htmlFor="boat-search">
            {role === "operator"
              ? view === "fleet"
                ? "Search your boats or routes"
                : "Search cargo or routes"
              : role === "control"
                ? "Search deliveries or routes"
                : "Search boats or routes"}
          </label>
          <input
            id="boat-search"
            placeholder={
              role === "operator"
                ? view === "fleet"
                  ? "Search your boats or routes…"
                  : "Search cargo or routes…"
                : role === "control"
                  ? "Search deliveries, cargo or routes…"
                  : "Search boats, routes or cargo…"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button aria-label="Search marketplace">
            <Search size={22} />
          </button>
        </form>
        {data?.demo_mode && (
          <label className="market-account">
            <span>Demo workspace</span>
            <select
              aria-label="Demo role"
              value={role}
              onChange={(e) => {
                setSearch("");
                setQuery("");
                setNotice("");
                setRole(e.target.value);
                navigate(
                  view === "tracking" ||
                    (e.target.value === "shipper" && role !== "shipper")
                    ? "tracking"
                    : "overview",
                );
              }}
            >
              {Object.entries(roles).map(([id, label]) => (
                <option key={id} value={id}>
                  {label}
                </option>
              ))}
            </select>
            <ChevronDown size={13} />
          </label>
        )}
        <button className="market-orders" onClick={() => navigate("tracking")}>
          <ShoppingBag size={24} />
          <span>
            Your<strong>bookings</strong>
          </span>
        </button>
      </header>
      <div className="market-nav">
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <button
              key={item}
              className={view === item ? "active" : ""}
              aria-current={view === item ? "page" : undefined}
              onClick={() =>
                item === "voice" && role === "operator"
                  ? listBoat()
                  : navigate(item)
              }
            >
              {item === "overview" && role === "operator"
                ? "Cargo requests"
                : item === "tracking" && role === "operator"
                  ? "My departures"
                  : item === "overview" && role === "control"
                    ? "Deliveries"
                    : item === "tracking" && role === "control"
                      ? "Delivery & impact"
                      : pageLabels[item]}
            </button>
          ))}
        </nav>
        <button
          className="market-post"
          onClick={() =>
            role === "operator"
              ? listBoat()
              : navigate(role === "control" ? "planner" : "posting")
          }
        >
          <Plus size={17} />
          {role === "operator"
            ? "List your boat"
            : role === "control"
              ? "Plan a delivery"
              : "Post cargo"}
        </button>
      </div>
      <div className="market-assurance">
        <span>
          <CheckCircle2 size={15} /> Cargo & boat matching
        </span>
        <span>
          <CalendarDays size={15} /> Planned departures
        </span>
        <span>
          <Leaf size={15} /> Road vs water comparison
        </span>
        {data?.demo_mode && (
          <span className="sample-pill">Local demo · Sample data</span>
        )}
      </div>
      <main id="main-content" className="market-main" tabIndex={-1}>
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
            <CheckCircle2 size={18} />
            {notice}
            <button
              aria-label="Dismiss notification"
              onClick={() => setNotice("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {!ready ? (
          error ? (
            <Empty>
              <p>Could not connect to the workspace.</p>
              <button
                className="button primary"
                onClick={() =>
                  load()
                    .then(() => setError(""))
                    .catch((e) => setError(e.message))
                }
              >
                Try again
              </button>
            </Empty>
          ) : (
            <Loading />
          )
        ) : (
          <>
            {role === "shipper" && view === "overview" && (
              <Marketplace
                data={data}
                search={search}
                clearSearch={() => {
                  setSearch("");
                  setQuery("");
                }}
                cargoId={cargoId}
                setCargoId={setCargoId}
                book={book}
                post={() => navigate("posting")}
              />
            )}
            {view === "posting" && role === "shipper" && (
              <Posting
                data={data}
                role={role}
                cancel={() => navigate("overview")}
                done={async (cargo) => {
                  await load();
                  setCargoId(cargo.id);
                  setSearch("");
                  setQuery("");
                  setNotice(
                    "Cargo posted. Choose a boat to compare prices and plan your delivery.",
                  );
                  navigate("overview");
                }}
              />
            )}
            {view === "cargo" && (
              <>
                <PageHeading
                  title="My cargo"
                  description="Post a load. Choose a boat. Get it moving."
                  action={
                    <button
                      className="button primary"
                      onClick={() => navigate("posting")}
                    >
                      <Plus size={17} />
                      Post cargo
                    </button>
                  }
                />
                <div className="market-cargo-grid">
                  {data.cargo.map((cargo: Cargo) => (
                    <article className="market-cargo-card" key={cargo.id}>
                      <Package size={25} />
                      <Badge value={cargo.status} />
                      <h2>
                        {title(cargo.cargo_type)} · {cargo.weight_tonnes} t
                      </h2>
                      <p>
                        {cargo.origin} → {cargo.destination}
                      </p>
                      <small>
                        Ready {date(cargo.ready_time)}
                        <br />
                        Deliver by {date(cargo.delivery_deadline)}
                      </small>
                      <button
                        className="button primary"
                        onClick={() => {
                          setCargoId(cargo.id);
                          navigate(
                            ["POSTED", "MATCHED", "QUOTED"].includes(
                              cargo.status,
                            )
                              ? "overview"
                              : "tracking",
                          );
                        }}
                      >
                        {["POSTED", "MATCHED", "QUOTED"].includes(cargo.status)
                          ? "Find a boat"
                          : "Track delivery"}
                        <ArrowRight size={16} />
                      </button>
                    </article>
                  ))}
                </div>
                {!data.cargo.length && (
                  <Empty>
                    No cargo yet. Post your first load to get started.
                  </Empty>
                )}
              </>
            )}
            {view === "coverage" && (
              <>
                <PageHeading
                  title="Built for the Backwater Cargo Exchange"
                  description="All five features from the challenge, in one connected marketplace."
                />
                <ChallengeCoverage
                  role={role}
                  setView={navigate}
                  switchRole={data.demo_mode ? switchRole : undefined}
                />
              </>
            )}
            {role === "operator" && data.demo_mode && (
              <label className="operator-account">
                Operator account
                <select
                  aria-label="Demo operator account"
                  value={operatorUser}
                  onChange={(e) => {
                    localStorage.setItem(
                      "jalayatra-operator-user",
                      e.target.value,
                    );
                    setOperatorUser(e.target.value);
                    setEditingListing("");
                    setVesselId("");
                    setSearch("");
                    setQuery("");
                    setNotice("");
                  }}
                >
                  <option value="demo-operator">Vembanad Freight Co.</option>
                  <option value="demo-pamba-operator">
                    Pamba Inland Logistics
                  </option>
                </select>
              </label>
            )}
            {view === "newboat" && role === "operator" && (
              <BoatRegistration
                data={data}
                cancel={() => navigate("fleet")}
                done={async (boatId) => {
                  await load();
                  setVesselId(boatId);
                  setSearch("");
                  setQuery("");
                  setNotice(
                    "Boat registered and availability saved. You can now receive cargo requests after certificate review.",
                  );
                  navigate("fleet");
                }}
              />
            )}
            {view === "voice" && role === "operator" && (
              <AvailabilityPosting
                key={`${operatorUser}-${editingListing}-${vesselId}`}
                data={data}
                vesselId={vesselId}
                listingId={editingListing}
                register={() => navigate("newboat")}
                cancel={() => navigate("fleet")}
                done={async (edited) => {
                  await load();
                  setNotice(
                    edited
                      ? "Boat availability updated. Your existing listing was saved."
                      : "Boat availability published. Your listing is ready for matching.",
                  );
                  setEditingListing("");
                  navigate("fleet");
                }}
              />
            )}
            {role === "operator" &&
              ["overview", "demand", "fleet", "tracking"].includes(view) && (
                <OperatorMarketplace
                  key={operatorUser}
                  data={data}
                  view={view}
                  search={search}
                  clearSearch={() => {
                    setSearch("");
                    setQuery("");
                  }}
                  act={act}
                  busy={busy}
                  setView={navigate}
                  list={listBoat}
                  edit={editListing}
                  register={() => navigate("newboat")}
                  switchRole={data.demo_mode ? switchRole : undefined}
                />
              )}
            {role === "control" &&
              ["overview", "providers", "tracking"].includes(view) && (
                <LogisticsMarketplace
                  data={data}
                  view={view}
                  search={search}
                  clearSearch={() => {
                    setSearch("");
                    setQuery("");
                  }}
                  act={act}
                  busy={busy}
                  setView={navigate}
                  switchRole={data.demo_mode ? switchRole : undefined}
                />
              )}
            {((role === "shipper" && ["planner", "tracking"].includes(view)) ||
              (role === "control" && view === "planner")) && (
              <>
                <PageHeading
                  title={
                    view === "planner"
                      ? "Plan your delivery"
                      : view === "tracking"
                        ? role === "control"
                          ? "Delivery & impact"
                          : "Your bookings"
                        : "Coordinate deliveries"
                  }
                  description={
                    view === "planner"
                      ? "Compare the delivered price, review the dates and request your booking."
                      : "Follow the next action on each delivery. Every approval is saved."
                  }
                  action={
                    view === "planner" && (
                      <button
                        className="button"
                        onClick={() => navigate("overview")}
                      >
                        <ArrowLeft size={16} />
                        Back to boats
                      </button>
                    )
                  }
                />
                <CargoLines
                  key={`${role}-${operatorUser}-${view === "planner" ? cargoId + vesselId : "bookings"}`}
                  data={data}
                  role={role}
                  act={act}
                  busy={busy}
                  view={
                    view === "planner" && role === "shipper" ? "overview" : view
                  }
                  initialCargoId={view === "planner" ? cargoId : ""}
                  initialVesselId={vesselId}
                  initialAvailabilityId={availabilityId}
                  newCargo={() => navigate("posting")}
                  replan={(id) => {
                    setCargoId(id);
                    setVesselId("");
                    setAvailabilityId("");
                    setSearch("");
                    setQuery("");
                    navigate(role === "shipper" ? "overview" : "planner");
                  }}
                  setView={navigate}
                  switchRole={data.demo_mode ? switchRole : undefined}
                />
              </>
            )}
          </>
        )}
      </main>
      <footer className="market-footer">
        <div>
          <Anchor size={22} />
          <strong>jalayatra</strong>
          <span>Moving Kerala’s cargo through its waterways.</span>
        </div>
        <p>
          Local prototype · Synthetic prices and emissions estimates · Provider
          responses are simulated
        </p>
      </footer>
    </div>
  );
}
function PageHeading({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="market-page-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
