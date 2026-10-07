import { useEffect, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Leaf,
  MapPin,
  Package,
  ShieldCheck,
  Ship,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { api, date, money, title, type Cargo, type Data } from "../api";
import { Empty } from "./UI";

type Props = {
  data: Data;
  search: string;
  clearSearch: () => void;
  cargoId: string;
  setCargoId: (id: string) => void;
  book: (cargo: string, boat: string, listing?: string) => void;
  post: () => void;
  operator?: boolean;
};
export default function Marketplace({
  data,
  search,
  clearSearch,
  cargoId,
  setCargoId,
  book,
  post,
  operator,
}: Props) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [capacity, setCapacity] = useState("0");
  const [sort, setSort] = useState("recommended");
  const [matched, setMatched] = useState<Data | null>(null);
  const [matchError, setMatchError] = useState("");
  const pending: Cargo[] = data.cargo.filter((c: Cargo) =>
    ["POSTED", "MATCHED", "QUOTED"].includes(c.status),
  );
  const selected =
    pending.find((c) => c.id === cargoId) ||
    pending.find((c) => c.id === "hero-cargo") ||
    pending[0];
  useEffect(() => {
    if (selected && selected.id !== cargoId) setCargoId(selected.id);
  }, [selected?.id, cargoId, setCargoId]);
  useEffect(() => {
    let current = true;
    setMatched(null);
    setMatchError("");
    if (selected && !operator)
      api(`/cargo/${selected.id}/matches`, "shipper")
        .then((r) => {
          if (current) setMatched(r);
        })
        .catch((e) => {
          if (current) setMatchError(e.message);
        });
    return () => {
      current = false;
    };
  }, [selected?.id, operator]);
  const recommendations = matched?.recommendations || [];
  const ranks = new Map<string, number>(
    recommendations.map((m: Data, i: number) => [m.vessel_id, i]),
  );
  const listings: Data[] = data.availability
    .map((listing: Data) => ({
      ...listing,
      vessel: data.vessels.find((v: Data) => v.id === listing.vessel_id),
    }))
    .filter((a: Data) => a.vessel && (operator || a.active));
  const matchingWindows = new Set<string>(
    recommendations.flatMap((m: Data) =>
      m.feasibility.terminal_options.map((p: Data) => p.availability_id),
    ),
  );
  const filtered = listings
    .filter(
      (a) =>
        (operator || !matched || matchingWindows.has(a.id)) &&
        (!origin || a.origin === origin) &&
        (!destination || a.destination === destination) &&
        a.capacity_tonnes >= Number(capacity) &&
        `${a.vessel.name} ${a.origin} ${a.destination} ${a.vessel.cargo_categories.join(" ")}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    )
    .sort((a, b) =>
      sort === "capacity"
        ? b.capacity_tonnes - a.capacity_tonnes
        : sort === "price"
          ? a.vessel.rate_per_tonne_km - b.vessel.rate_per_tonne_km
          : (ranks.get(a.vessel_id) ?? 99) - (ranks.get(b.vessel_id) ?? 99),
    );
  const reset = () => {
    setOrigin("");
    setDestination("");
    setCapacity("0");
    clearSearch();
  };
  return (
    <div className="marketplace">
      {!operator && (
        <>
          <section className="market-hero">
            <div className="market-hero-copy">
              <span className="market-kicker">
                KERALA’S WATERWAY MARKETPLACE
              </span>
              <h1>
                Your cargo.
                <br />
                The right boat.
                <br />
                <em>One easy booking.</em>
              </h1>
              <p>
                Find available boats, compare the full delivery cost and plan
                your next shipment.
              </p>
              <button className="button market-yellow" onClick={post}>
                <PlusIcon />
                Post your cargo
                <ArrowRight size={18} />
              </button>
              <span className="hero-note">
                Already have cargo? Choose it below to find a match.
              </span>
            </div>
            <div className="market-hero-art">
              <BoatArt large />
              <div className="hero-route">
                <MapPin size={18} />
                <div>
                  <small>EXPLORE THE BACKWATERS</small>
                  <strong>
                    Kochi <ArrowRight size={16} /> Alappuzha
                  </strong>
                </div>
              </div>
              <span className="hero-watermark">GO BY WATER.</span>
            </div>
          </section>
          <div className="market-benefits">
            <div>
              <Package />
              <span>
                <strong>Post your cargo</strong>
                <small>Tell us what, where and when</small>
              </span>
            </div>
            <div>
              <Ship />
              <span>
                <strong>Find your boat</strong>
                <small>Match capacity, route and dates</small>
              </span>
            </div>
            <div>
              <CalendarDays />
              <span>
                <strong>Plan & book</strong>
                <small>Approve a price and departure</small>
              </span>
            </div>
            <div>
              <Leaf />
              <span>
                <strong>Compare the impact</strong>
                <small>Road and water, side by side</small>
              </span>
            </div>
          </div>
          <section className="market-shipment">
            <div>
              <Package size={22} />
              <div>
                <strong>What are you sending?</strong>
                <small>Choose cargo to see recommended boats.</small>
              </div>
            </div>
            {pending.length ? (
              <label>
                <span className="sr-only">Choose cargo for matching</span>
                <select
                  aria-label="Choose cargo for matching"
                  value={selected?.id || ""}
                  onChange={(e) => setCargoId(e.target.value)}
                >
                  {pending.map((c) => (
                    <option key={c.id} value={c.id}>
                      {title(c.cargo_type)} · {c.weight_tonnes} t · {c.origin} →{" "}
                      {c.destination}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <button className="button market-yellow" onClick={post}>
                Post your first cargo
                <ArrowRight size={16} />
              </button>
            )}
          </section>
        </>
      )}
      <div className="market-catalog-head">
        <div>
          <span className="market-kicker">BOAT AVAILABILITY LISTING</span>
          <h2>
            {operator
              ? "Your published availability"
              : "Find a boat for your cargo"}
          </h2>
          <p>
            {filtered.length} listings{search && ` for “${search}”`} · Routes
            across Kerala’s backwaters
          </p>
        </div>
        <label>
          Sort by
          <select
            aria-label="Sort boats"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="recommended">✨ AI Shortlisted (Optimal Match)</option>
            <option value="capacity">Highest capacity</option>
            <option value="price">Lowest base rate</option>
          </select>
        </label>
      </div>
      <div className="market-catalog">
        <aside className="market-filters">
          <h3>
            <SlidersHorizontal size={18} />
            Filter boats
          </h3>
          <label>
            From
            <select
              aria-label="Filter from"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            >
              <option value="">Any pickup</option>
              {[...new Set(listings.map((a) => a.origin))].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label>
            To
            <select
              aria-label="Filter to"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            >
              <option value="">Any destination</option>
              {[...new Set(listings.map((a) => a.destination))].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label>
            Minimum capacity
            <select
              aria-label="Minimum boat capacity"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
            >
              <option value="0">Any capacity</option>
              <option value="50">50 tonnes</option>
              <option value="100">100 tonnes</option>
              <option value="150">150 tonnes</option>
            </select>
          </label>
          <button className="market-text-button" onClick={reset}>
            Clear all filters
          </button>
          <div className="filter-note">
            <ShieldCheck size={24} />
            <strong>Safety before sailing</strong>
            <p>
              Route, cargo, dimensions and dates are checked before a booking is
              accepted.
            </p>
          </div>
        </aside>
        <div>
          <div className="market-results-note">
            <CheckCircle2 size={17} />
            {operator
              ? "Your listings are visible to cargo matching."
              : matched
                ? `${recommendations.length} boats pass the cargo & route checks. Full delivery feasibility is checked at checkout.`
                : selected
                  ? "Checking boats against your cargo…"
                  : "Browse availability. Post cargo to compare full delivery prices."}
          </div>
          {matchError && (
            <p role="alert" className="alert error">
              {matchError}
            </p>
          )}
          <div className="market-boat-grid">
            {filtered.map((a, index) => {
              const v = a.vessel;
              const vesselMatch = recommendations.find(
                (m: Data) => m.vessel_id === v.id,
              );
              const windowMatches =
                vesselMatch?.feasibility.terminal_options.some(
                  (p: Data) => p.availability_id === a.id,
                );
              const rank = windowMatches ? ranks.get(v.id) : undefined;
              return (
                <article className="market-boat-card" key={a.id}>
                  <div className={`boat-picture boat-tone-${index % 3}`}>
                    <BoatArt />
                    <span
                      className={rank === 0 ? "boat-label best" : "boat-label"}
                    >
                      {rank === 0
                        ? `✨ AI Shortlisted #1 · ${Math.round(vesselMatch?.score || 85)}% Match`
                        : rank !== undefined
                          ? `AI Shortlisted · ${Math.round(vesselMatch?.score || 70)}% Match`
                          : `${title(v.vessel_type)} · ${a.capacity_tonnes} t`}
                    </span>
                  </div>
                  <div className="boat-card-body">
                    <small className="boat-operator">
                      {v.organization_id === "operator-org"
                        ? "Vembanad Freight Co."
                        : v.organization_id === "other-operator"
                          ? "Pamba Inland Logistics"
                          : "Inland boat operator"}
                    </small>
                    <h3>{v.name}</h3>
                    <p className="boat-route">
                      <MapPin size={15} />
                      {a.origin}
                      <ArrowRight size={14} />
                      {a.destination}
                    </p>
                    <div className="boat-specs">
                      <span>
                        <strong>{a.capacity_tonnes} t</strong>Available capacity
                      </span>
                      <span>
                        <strong>{a.volume_m3} m³</strong>Cargo volume
                      </span>
                    </div>
                    {vesselMatch && rank !== undefined && (
                      <div
                        style={{
                          background: "#f0fdf4",
                          border: "1px solid #bbf7d0",
                          borderRadius: "6px",
                          padding: "6px 10px",
                          margin: "6px 0",
                          fontSize: "0.8rem",
                          color: "#166534",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "5px",
                            fontWeight: 600,
                            marginBottom: "2px",
                          }}
                        >
                          <Sparkles size={13} color="#15803d" />
                          <span>AI Shortlist Rationale ({Math.round(vesselMatch.score)}% fit)</span>
                        </div>
                        <div
                          style={{
                            fontSize: "0.74rem",
                            color: "#14532d",
                            lineHeight: "1.25",
                          }}
                        >
                          {vesselMatch.reasons?.[1] || "Feasible draft, capacity fit & optimal emissions reduction"}
                        </div>
                      </div>
                    )}
                    <p className="boat-dates">
                      <CalendarDays size={15} />
                      {date(a.available_from)}
                      <br />
                      to {date(a.available_until)}
                    </p>
                    <div className="boat-price">
                      <strong>
                        {money(v.rate_per_tonne_km)}
                        <small> / tonne-km</small>
                      </strong>
                      <span>Base boat rate · Full price at checkout</span>
                    </div>
                    <button
                      className={`button ${operator ? "" : "market-yellow"}`}
                      disabled={!operator && Boolean(selected) && !matched}
                      onClick={() =>
                        operator
                          ? book("", v.id)
                          : selected
                            ? book(selected.id, v.id, a.id)
                            : post()
                      }
                    >
                      {operator
                        ? "Update availability"
                        : selected
                          ? "Compare & book"
                          : "Post cargo to book"}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          {matched?.rejected && matched.rejected.length > 0 && !operator && (
            <details
              style={{
                marginTop: "20px",
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                padding: "12px 16px",
              }}
            >
              <summary
                style={{
                  cursor: "pointer",
                  fontWeight: 600,
                  color: "#374151",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <ShieldCheck size={16} color="#059669" />
                <span>
                  AI Feasibility Exclusions: {matched.rejected.length} boat(s) excluded for navigation safety
                </span>
              </summary>
              <div style={{ marginTop: "10px", fontSize: "0.85rem", color: "#4b5563" }}>
                {matched.rejected.map((r: Data) => (
                  <div key={r.vessel_id} style={{ padding: "6px 0", borderBottom: "1px solid #f3f4f6" }}>
                    <strong style={{ color: "#111827" }}>{r.vessel_name}:</strong>{" "}
                    {r.feasibility?.reasons?.join("; ") || "Exceeded waterway safety limits"}
                  </div>
                ))}
              </div>
            </details>
          )}
          {!filtered.length && (
            <Empty>
              <Ship size={35} />
              <h3>No boats match these filters</h3>
              <p>Try a different route or reduce the minimum capacity.</p>
              <button className="button" onClick={reset}>
                Clear filters
              </button>
            </Empty>
          )}
        </div>
      </div>
    </div>
  );
}
function PlusIcon() {
  return <Package size={19} />;
}
export function BoatArt({ large = false }: { large?: boolean }) {
  return (
    <svg
      className={large ? "boat-art large" : "boat-art"}
      viewBox="0 0 560 280"
      role="img"
      aria-label="Illustration of an inland cargo boat"
    >
      <path
        d="M0 234Q65 211 130 234T260 234T390 234T560 234V280H0Z"
        fill="#9acacb"
      />
      <path
        d="M0 254Q65 231 130 254T260 254T390 254T560 254"
        fill="none"
        stroke="#fff"
        strokeWidth="3"
        opacity=".55"
      />
      <path d="M63 185H497L469 227H105Z" fill="#254c54" />
      <path d="M63 185H497L486 201H80Z" fill="#17353e" />
      <path d="M92 185V167H454V185" fill="#d7e4dd" />
      <rect x="135" y="113" width="75" height="54" rx="3" fill="#c8904c" />
      <path
        d="M146 113V167M163 113V167M180 113V167M198 113V167"
        stroke="#a86f39"
        strokeWidth="3"
      />
      <rect x="214" y="113" width="75" height="54" rx="3" fill="#e6bc76" />
      <path
        d="M225 113V167M243 113V167M260 113V167M277 113V167"
        stroke="#caa05f"
        strokeWidth="3"
      />
      <rect x="293" y="113" width="70" height="54" rx="3" fill="#86aaa4" />
      <path
        d="M304 113V167M322 113V167M339 113V167M354 113V167"
        stroke="#638e87"
        strokeWidth="3"
      />
      <path d="M372 100H436V167H372Z" fill="#f5f3e8" />
      <path d="M367 96H442V106H367Z" fill="#335d63" />
      <rect x="382" y="114" width="16" height="20" fill="#81b8c3" />
      <rect x="405" y="114" width="20" height="20" fill="#81b8c3" />
      <path d="M389 96V62" stroke="#335d63" strokeWidth="4" />
      <path d="M390 63H419L405 75H390Z" fill="#e4b456" />
      <path d="M110 174H363" stroke="#fff" strokeWidth="3" />
      <circle cx="102" cy="201" r="7" fill="#eee9db" />
      <circle cx="448" cy="201" r="7" fill="#eee9db" />
    </svg>
  );
}
