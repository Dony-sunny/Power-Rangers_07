import { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  MapPin,
  Package,
  Pause,
  Pencil,
  Play,
  Plus,
  ShieldCheck,
  Ship,
} from "lucide-react";
import { api, date, money, title, type Act, type Data } from "../api";
import { Badge, Empty, Loading } from "./UI";
import { BoatArt } from "./Marketplace";

type Props = {
  data: Data;
  view: string;
  search: string;
  clearSearch: () => void;
  act: Act;
  busy: boolean;
  setView: (v: string) => void;
  list: (boat?: string) => void;
  edit: (listing: string, boat: string) => void;
  register: () => void;
  switchRole?: (role: string, vesselId?: string) => void;
};
export default function OperatorMarketplace({
  data,
  view,
  search,
  clearSearch,
  act,
  busy,
  setView,
  list,
  edit,
  register,
  switchRole,
}: Props) {
  const [snapshot, setSnapshot] = useState<Data | null>(null),
    [error, setError] = useState("");
  const [boatId, setBoatId] = useState("");
  const [demand, setDemand] = useState<Data | null>(null),
    [demandError, setDemandError] = useState("");
  const refresh = useCallback(async () => {
    try {
      setSnapshot(await api("/lines", "operator"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh, data]);
  useEffect(() => {
    let current = true;
    setDemand(null);
    setDemandError("");
    const id = boatId || data.vessels[0]?.id;
    if (view === "demand" && id)
      api(`/vessels/${id}/opportunities`, "operator")
        .then((result) => {
          if (current) setDemand(result);
        })
        .catch((e) => {
          if (current) setDemandError(e.message);
        });
    return () => {
      current = false;
    };
  }, [view, boatId, data]);
  const run: Act = (task, message) =>
    act(async () => {
      try {
        await task();
      } finally {
        await refresh();
      }
    }, message);
  const voyages: Data[] = snapshot?.departures || [];
  const pending = voyages.filter(
    (v) => v.status === "HELD" && !v.operator_accepted,
  );
  const ownListings: Data[] = data.availability;
  const boats: Data[] = data.vessels.filter((v: Data) =>
    `${v.name} ${v.cargo_categories.join(" ")} ${ownListings
      .filter((a) => a.vessel_id === v.id)
      .map((a) => `${a.origin} ${a.destination}`)
      .join(" ")}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  const displayed = voyages.filter(
    (v) =>
      (view === "tracking" || v.status === "HELD") &&
      (!boatId || v.vessel_id === boatId) &&
      `${v.vessel_name} ${v.members.map((m: Data) => `${m.cargo_type} ${m.origin} ${m.destination}`).join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const chosenBoat = data.vessels.find(
    (v: Data) => v.id === (boatId || data.vessels[0]?.id),
  );
  return (
    <div className="operator-marketplace">
      {view === "overview" && (
        <>
          <section className="market-hero operator-hero">
            <div className="market-hero-copy">
              <span className="market-kicker">YOUR BOAT BUSINESS</span>
              <h1>
                Your boat.
                <br />
                More cargo.
                <br />
                <em>Keep it moving.</em>
              </h1>
              <p>
                Publish your available space, discover compatible cargo and
                accept the right departure.
              </p>
              <div className="button-row">
                <button className="button market-yellow" onClick={() => list()}>
                  <Plus size={18} />
                  List boat availability
                </button>
                <button className="button" onClick={() => setView("demand")}>
                  Find cargo
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
            <div className="market-hero-art">
              <BoatArt large />
              <div className="hero-route">
                <Ship size={22} />
                <div>
                  <small>YOUR FLEET</small>
                  <strong>{data.vessels.length} registered boats</strong>
                </div>
              </div>
              <span className="hero-watermark">READY FOR THE NEXT LOAD.</span>
            </div>
          </section>
          <div className="operator-shortcuts">
            <button onClick={() => setView("fleet")}>
              <Ship size={23} />
              <strong>{ownListings.filter((a) => a.active).length}</strong>
              <span>Published windows</span>
              <ArrowRight size={16} />
            </button>
            <button
              onClick={() =>
                document
                  .getElementById("operator-requests")
                  ?.scrollIntoView({ behavior: "instant" })
              }
            >
              <Package size={23} />
              <strong>{pending.length}</strong>
              <span>Requests to review</span>
              <ArrowRight size={16} />
            </button>
            <button onClick={() => setView("tracking")}>
              <CalendarDays size={23} />
              <strong>
                {
                  voyages.filter(
                    (v) =>
                      ["HELD", "CONFIRMED"].includes(v.status) &&
                      v.operator_accepted,
                  ).length
                }
              </strong>
              <span>Accepted departures</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </>
      )}
      {view === "fleet" ? (
        <>
          <div className="market-page-heading">
            <div>
              <span className="market-kicker">YOUR FLEET & LISTINGS</span>
              <h1>My boat listings</h1>
              <p>
                All your registered boats, with routes and available dates in
                one place.
              </p>
            </div>
            <button className="button market-yellow" onClick={() => list()}>
              <Plus size={17} />
              List boat availability
            </button>
          </div>
          {search && (
            <p className="operator-search-note">
              Results for “{search}”{" "}
              <button className="market-text-button" onClick={clearSearch}>
                Clear search
              </button>
            </p>
          )}
          <div className="button-row">
            <button className="button market-yellow" onClick={register}>
              <Plus size={17} />
              Add a new boat
            </button>
          </div>
          <div className="operator-fleet-grid">
            {boats.map((boat, index) => {
              const listings = ownListings.filter(
                (a) => a.vessel_id === boat.id,
              );
              return (
                <article className="operator-boat-card" key={boat.id}>
                  <div className={`boat-picture boat-tone-${index % 3}`}>
                    <BoatArt />
                    <span className="boat-label">
                      {title(boat.vessel_type)}
                    </span>
                  </div>
                  <div className="operator-boat-content">
                    <div className="operator-boat-title">
                      <h2>{boat.name}</h2>
                      <span>
                        {listings.filter((a) => a.active).length} published
                        windows
                      </span>
                    </div>
                    <div className="boat-specs">
                      <span>
                        <strong>{boat.max_capacity_tonnes} t</strong>Maximum
                        capacity
                      </span>
                      <span>
                        <strong>{boat.max_volume_m3} m³</strong>Cargo space
                      </span>
                      <span>
                        <strong>{money(boat.rate_per_tonne_km)}</strong>Base
                        rate / tonne-km
                      </span>
                    </div>
                    {listings.length ? (
                      listings.map((a) => (
                        <div
                          className={`operator-window ${a.active ? "" : "paused"}`}
                          key={a.id}
                          data-testid="operator-window"
                        >
                          <div className="operator-window-title">
                            <strong>
                              {a.origin}
                              <ArrowRight size={14} />
                              {a.destination}
                            </strong>
                            <span
                              className={`window-state ${a.active ? "published" : ""}`}
                            >
                              {a.active ? "Published" : "Paused"}
                            </span>
                          </div>
                          <p>
                            <CalendarDays size={15} />
                            {date(a.available_from)} to{" "}
                            {date(a.available_until)}
                          </p>
                          <p>
                            {a.capacity_tonnes} t available · {a.volume_m3} m³
                          </p>
                          <div className="operator-window-actions">
                            <button
                              className="button small"
                              disabled={busy}
                              onClick={() => edit(a.id, boat.id)}
                            >
                              <Pencil size={14} />
                              Edit availability
                            </button>
                            <button
                              className="button small"
                              disabled={busy}
                              onClick={() =>
                                run(
                                  () =>
                                    api(
                                      `/availability/${a.id}/visibility?active=${!a.active}`,
                                      "operator",
                                      {},
                                    ),
                                  a.active
                                    ? "Listing paused. Cargo owners won’t see this window."
                                    : "Listing published again.",
                                )
                              }
                            >
                              {a.active ? (
                                <Pause size={14} />
                              ) : (
                                <Play size={14} />
                              )}{" "}
                              {a.active ? "Pause listing" : "Publish listing"}
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="operator-no-window">
                        <Clock3 size={22} />
                        <strong>No availability published yet</strong>
                        <p>
                          Add a route and dates so cargo owners can find this
                          boat.
                        </p>
                      </div>
                    )}
                    <button
                      className="button market-yellow"
                      onClick={() => list(boat.id)}
                    >
                      <Plus size={16} />
                      Add availability window
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          {!boats.length && (
            <Empty>
              <Ship size={30} />
              <h3>No boats match your search</h3>
              <button className="button" onClick={clearSearch}>
                Clear search
              </button>
            </Empty>
          )}
        </>
      ) : view === "demand" ? (
        <>
          <div className="market-page-heading">
            <div>
              <span className="market-kicker">MATCHING RECOMMENDATIONS</span>
              <h1>Find cargo for your boat</h1>
              <p>
                Explore loads that fit your boat’s route, capacity and available
                dates.
              </p>
            </div>
            <button className="button" onClick={() => setView("fleet")}>
              Manage availability
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="operator-demand-toolbar">
            <label>
              Find cargo for
              <select
                aria-label="Find cargo for boat"
                value={boatId || data.vessels[0]?.id || ""}
                onChange={(e) => setBoatId(e.target.value)}
              >
                {data.vessels.map((v: Data) => (
                  <option key={v.id} value={v.id}>
                    {v.name} · {v.max_capacity_tonnes} t
                  </option>
                ))}
              </select>
            </label>
            <p>
              <ShieldCheck size={18} />
              These loads pass the cargo and route checks. A booking checks the
              full departure plan.
            </p>
          </div>
          {demandError && (
            <div className="alert error" role="alert">
              {demandError}
            </div>
          )}
          {!demand && !demandError && chosenBoat && <Loading />}
          <div className="market-cargo-grid">
            {demand?.cargo
              .filter((c: Data) =>
                `${c.cargo_type} ${c.origin} ${c.destination}`
                  .toLowerCase()
                  .includes(search.toLowerCase()),
              )
              .map((c: Data) => (
                <article className="operator-demand-card" key={c.id}>
                  <div className="operator-demand-icon">
                    <Package size={26} />
                    <span>Compatible cargo</span>
                  </div>
                  <h2>
                    {title(c.cargo_type)} · {c.weight_tonnes} t
                  </h2>
                  <p className="boat-route">
                    <MapPin size={16} />
                    {c.origin}
                    <ArrowRight size={16} />
                    {c.destination}
                  </p>
                  <div className="operator-demand-price">
                    <small>Estimated water freight</small>
                    <strong>{money(c.estimated_freight_revenue)}</strong>
                    <small>
                      Water leg estimate · Full price is reviewed with the
                      request
                    </small>
                  </div>
                  <p className="boat-dates">
                    <CalendarDays size={16} />
                    Estimated arrival {date(c.eta)}
                  </p>
                  <details>
                    <summary>How to book this cargo</summary>
                    <p>
                      The cargo owner chooses your boat and submits a booking
                      request. Once requested, review and accept it in Cargo
                      requests.
                    </p>
                  </details>
                  <div className="button-row">
                    <button
                      className="button"
                      onClick={() => setView("overview")}
                    >
                      View cargo requests
                      <ArrowRight size={16} />
                    </button>
                    {switchRole && (
                      <button
                        type="button"
                        className="button small"
                        onClick={() => switchRole("shipper")}
                      >
                        Book as cargo owner <ArrowRight size={14} />
                      </button>
                    )}
                  </div>
                </article>
              ))}
          </div>
          {demand &&
            !demand.cargo.some((c: Data) =>
              `${c.cargo_type} ${c.origin} ${c.destination}`
                .toLowerCase()
                .includes(search.toLowerCase()),
            ) && (
              <Empty>
                <Package size={30} />
                <h3>No matching cargo right now</h3>
                <p>
                  {search
                    ? "Try another search or choose another boat."
                    : "Publish another availability window or choose a different boat."}
                </p>
                <div className="button-row">
                  <button className="button" onClick={clearSearch}>
                    Clear search
                  </button>
                  <button
                    className="button market-yellow"
                    onClick={() => list(chosenBoat?.id)}
                  >
                    List availability
                  </button>
                </div>
              </Empty>
            )}
        </>
      ) : (
        <section id="operator-requests">
          <div className="operator-section-head">
            <div>
              <span className="market-kicker">
                {view === "tracking"
                  ? "SCHEDULES & DELIVERY PROGRESS"
                  : "CARGO REQUESTS"}
              </span>
              <h1>
                {view === "tracking"
                  ? "My departures"
                  : "Review your cargo requests"}
              </h1>
              <p>
                {view === "tracking"
                  ? "Follow your accepted departures and completed deliveries."
                  : "Review the cargo, dates and approved revenue before accepting a departure."}
              </p>
            </div>
            <label>
              Show boat
              <select
                aria-label="Filter departure boat"
                value={boatId}
                onChange={(e) => setBoatId(e.target.value)}
              >
                <option value="">All my boats</option>
                {data.vessels.map((v: Data) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {error && (
            <div className="alert error" role="alert">
              {error}
              <button className="button small" onClick={refresh}>
                Try again
              </button>
            </div>
          )}
          {!snapshot && !error && <Loading />}
          <div className="operator-request-grid">
            {displayed.map((voyage) => (
              <OperatorRequest
                key={voyage.id}
                voyage={voyage}
                busy={busy}
                act={run}
                switchRole={switchRole}
              />
            ))}
          </div>
          {snapshot && !displayed.length && (
            <div className="operator-empty">
              <Package size={34} />
              <h2>
                {search
                  ? "No requests match your search"
                  : view === "tracking"
                    ? "No departures yet"
                    : "No cargo requests yet"}
              </h2>
              <p>
                {search
                  ? "Clear the search or try another boat."
                  : ownListings.some((a) => (!boatId || a.vessel_id === boatId) && a.active)
                    ? `Your boat’s available dates are published and active in the marketplace! Waiting for a cargo owner to choose ${boatId ? data.vessels.find((v: Data) => v.id === boatId)?.name || "your boat" : "your boat"} and submit a departure request.`
                    : "Publish your available dates so cargo owners can discover your boat and request a departure."}
              </p>
              {boatId && voyages.length > 0 && (
                <div style={{ margin: "14px 0", padding: "12px", background: "#edf5ef", borderRadius: "8px" }}>
                  <p style={{ margin: "0 0 8px", fontSize: "13px" }}>
                    There are {voyages.length} departure request(s) on other boats in your account.
                  </p>
                  <button
                    type="button"
                    className="button small"
                    onClick={() => setBoatId("")}
                  >
                    Show all boats
                  </button>
                </div>
              )}
              <div className="button-row">
                {search && (
                  <button className="button" onClick={clearSearch}>
                    Clear search
                  </button>
                )}
                {ownListings.some((a) => (!boatId || a.vessel_id === boatId) && a.active) && switchRole && (
                  <button
                    type="button"
                    className="button market-yellow"
                    onClick={() => switchRole("shipper")}
                  >
                    Switch to Cargo owner to book this boat
                    <ArrowRight size={16} />
                  </button>
                )}
                <button className="button" onClick={() => list()}>
                  List boat availability
                  <ArrowRight size={16} />
                </button>
                <button className="button" onClick={() => setView("demand")}>
                  Browse matching cargo
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
function OperatorRequest({
  voyage,
  busy,
  act,
  switchRole,
}: {
  voyage: Data;
  busy: boolean;
  act: Act;
  switchRole?: Props["switchRole"];
}) {
  const held = voyage.status === "HELD";
  const [acknowledgeShortfall, setAcknowledgeShortfall] = useState(false);
  const shortfall = !voyage.accepted_economics.covers_modeled_costs;
  const ready = voyage.owners_ready && (!shortfall || acknowledgeShortfall);
  const next = held
    ? !voyage.owners_ready
      ? "Waiting for cargo owners to approve every quote."
      : !voyage.operator_accepted
        ? ready
          ? "Cargo owners approved. Review the load and accept this departure."
          : "Review the estimated shortfall below. You can accept this price or decline the departure."
        : "You accepted this departure. The coordinator will confirm the delivery team."
    : voyage.next_action;
  return (
    <article className="operator-request-card" data-testid="departure">
      <div className="operator-request-top">
        <div>
          <Ship size={23} />
          <h2>{voyage.vessel_name}</h2>
        </div>
        <Badge value={voyage.status} />
      </div>
      <div className="operator-request-dates">
        <div>
          <small>Departure</small>
          <strong>{date(voyage.departure)}</strong>
        </div>
        <div>
          <small>Total load</small>
          <strong>
            {voyage.weight_tonnes} t{" "}
            <span>· {(voyage.utilization * 100).toFixed(0)}% capacity</span>
          </strong>
        </div>
      </div>
      <div className="operator-request-loads">
        {voyage.members.map((m: Data) => (
          <div key={m.cargo_id}>
            <Package size={17} />
            <div>
              <strong>
                {title(m.cargo_type)} · {m.weight_tonnes} t
              </strong>
              <p>
                {m.origin} → {m.destination}
              </p>
              <small>Arrives {date(m.eta)}</small>
            </div>
            <span className={`cargo-approval ${m.accepted ? "approved" : ""}`}>
              {m.accepted ? "Quote approved" : "Awaiting owner"}
            </span>
          </div>
        ))}
      </div>
      <div className="operator-request-money">
        <div>
          <small>Approved delivery revenue</small>
          <strong>
            {money(voyage.accepted_economics.revenue_minor / 100)}
          </strong>
        </div>
        <div>
          <small>Estimated sailing contribution</small>
          <strong>
            {money(voyage.accepted_economics.contribution_minor / 100)}
          </strong>
        </div>
      </div>
      <p className="operator-earnings-note">
        {voyage.accepted_economics.covers_modeled_costs
          ? "Accepted delivery revenue covers modeled voyage costs."
          : "Accepted delivery revenue does not yet cover modeled voyage costs."}
      </p>
      <div className="operator-next-action">
        <CheckCircle2 size={19} />
        <p>{next}</p>
      </div>
      {held && !voyage.owners_ready && (
        <div className="operator-blocker-handoff">
          <p className="operator-blocker">
            Acceptance unlocks after every cargo owner approves their quote.
          </p>
          {switchRole && (
            <button
              type="button"
              className="button small"
              onClick={() => switchRole("shipper")}
            >
              Open cargo owner workspace to approve quote{" "}
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      )}
      {voyage.operator_accepted && (
        <p className="operator-accepted">
          Operator accepted version {voyage.version} <CheckCircle2 size={17} />
        </p>
      )}
      {held &&
        voyage.owners_ready &&
        !voyage.operator_accepted &&
        shortfall && (
          <label className="operator-shortfall-choice">
            <input
              type="checkbox"
              checked={acknowledgeShortfall}
              onChange={(e) => setAcknowledgeShortfall(e.target.checked)}
            />
            <span>
              I accept the approved price despite the estimated sailing
              shortfall of{" "}
              {money(-voyage.accepted_economics.contribution_minor / 100)}.
            </span>
          </label>
        )}
      {held && !voyage.operator_accepted && (
        <div className="operator-request-actions">
          <button
            className="button market-yellow"
            disabled={busy || !ready}
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/operator-response`, "operator", {
                    version: voyage.version,
                    accept: true,
                    acknowledge_shortfall: acknowledgeShortfall,
                  }),
                "Departure accepted. The coordinator can now arrange the delivery team.",
              )
            }
          >
            Accept reviewed departure
            <ArrowRight size={16} />
          </button>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/operator-response`, "operator", {
                    version: voyage.version,
                    accept: false,
                  }),
                "Departure declined. Its local allocations were released.",
              )
            }
          >
            Decline departure
          </button>
        </div>
      )}
      {held && switchRole && voyage.operator_accepted && (
        <div className="operator-handoff">
          <span>Demo · Continue the delivery workflow</span>
          <button
            className="market-text-button"
            onClick={() => switchRole("control")}
          >
            Open logistics coordinator workspace <ArrowRight size={14} />
          </button>
        </div>
      )}
      <details className="operator-request-details">
        <summary>Schedule, costs & approval details</summary>
        <dl>
          <div>
            <dt>Loading starts</dt>
            <dd>{date(voyage.loading_start)}</dd>
          </div>
          <div>
            <dt>Water arrival / unloading complete</dt>
            <dd>{date(voyage.water_end)}</dd>
          </div>
          <div>
            <dt>Booking cutoff</dt>
            <dd>{date(voyage.cutoff)}</dd>
          </div>
          {held && (
            <div>
              <dt>Quote expires</dt>
              <dd>{date(voyage.expires_at)}</dd>
            </div>
          )}
          <div>
            <dt>Delivery coordinator</dt>
            <dd>{voyage.service_owner}</dd>
          </div>
          <div>
            <dt>Truck / terminal responses</dt>
            <dd>
              {voyage.accepted_job_count}/{voyage.job_count} accepted ·
              Simulated
            </dd>
          </div>
          <div>
            <dt>Provider and operating allowances</dt>
            <dd>
              {money(voyage.accepted_economics.operating_cost_minor / 100)}
            </dd>
          </div>
        </dl>
        <p>{voyage.accepted_economics.basis}</p>
        {voyage.members.map((m: Data) => (
          <p key={m.cargo_id}>
            {title(m.cargo_type)}: {title(m.status)}
            {m.receipt
              ? ` · ${m.receipt.quantity_tonnes} t received by ${m.receipt.receiver_name}`
              : ""}
          </p>
        ))}
      </details>
    </article>
  );
}
