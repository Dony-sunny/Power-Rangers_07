import { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Leaf,
  Package,
  Plus,
  Ship,
  Truck,
} from "lucide-react";
import { api, date, money, title, type Act, type Data } from "../api";
import { Badge, Empty, Loading, Stat } from "./UI";
import { BoatArt } from "./Marketplace";
type Props = {
  data: Data;
  view: string;
  search: string;
  clearSearch: () => void;
  act: Act;
  busy: boolean;
  setView: (view: string) => void;
  switchRole?: (role: string, vesselId?: string) => void;
};
export default function LogisticsMarketplace({
  data,
  view,
  search,
  clearSearch,
  act,
  busy,
  setView,
  switchRole,
}: Props) {
  const [snapshot, setSnapshot] = useState<Data | null>(null),
    [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const refresh = useCallback(async () => {
    try {
      setSnapshot(await api("/lines", "control"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh, data]);
  const run: Act = (task, message) =>
    act(async () => {
      try {
        await task();
      } finally {
        await refresh();
      }
    }, message);
  const voyages: Data[] = snapshot?.departures || [];
  const filtered = voyages.filter(
    (v) =>
      `${v.vessel_name} ${v.id} ${v.members.map((m: Data) => `${m.cargo_type} ${m.origin} ${m.destination}`).join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (view === "providers" ||
        filter === "all" ||
        (filter === "pending" && v.status === "HELD") ||
        (filter === "active" && v.status === "CONFIRMED") ||
        (filter === "completed" && v.status === "COMPLETED")),
  );
  const priority: Record<string, number> = {
    HELD: 0,
    DISRUPTED: 1,
    CONFIRMED: 2,
    COMPLETED: 3,
  };
  filtered.sort(
    (a, b) =>
      (priority[a.status] ?? 4) - (priority[b.status] ?? 4) ||
      a.departure.localeCompare(b.departure),
  );
  const pendingJobs = voyages.flatMap((v) =>
    v.status === "HELD"
      ? v.jobs.filter((j: Data) => j.status === "PENDING")
      : [],
  );
  return (
    <div className="logistics-marketplace">
      {view === "overview" && (
        <>
          <section className="market-hero logistics-hero">
            <div className="market-hero-copy">
              <span className="market-kicker">YOUR LOGISTICS WORKSPACE</span>
              <h1>
                Plan the handoffs.
                <br />
                Keep cargo moving.
                <br />
                <em>Deliver with clarity.</em>
              </h1>
              <p>
                Confirm the delivery team, follow each departure and record
                cargo received—all in one place.
              </p>
              <div className="button-row">
                <button
                  className="button market-yellow"
                  onClick={() => setView("planner")}
                >
                  <Plus size={17} />
                  Plan a delivery
                </button>
                {data.demo_mode && (
                  <button
                    className="button"
                    disabled={busy}
                    onClick={() =>
                      run(
                        () => api("/demo/populate", "admin", {}),
                        "Sample deliveries added. Existing records are preserved.",
                      )
                    }
                  >
                    Add demo deliveries
                    <Package size={16} />
                  </button>
                )}
              </div>
            </div>
            <div className="market-hero-art">
              <BoatArt large />
              <div className="hero-route">
                <Truck size={21} />
                <div>
                  <small>ONE CONNECTED DELIVERY</small>
                  <strong>
                    Pickup
                    <ArrowRight size={13} />
                    Boat
                    <ArrowRight size={13} />
                    Delivery
                  </strong>
                </div>
              </div>
              <span className="hero-watermark">
                EVERY HANDOFF, ACCOUNTED FOR.
              </span>
            </div>
          </section>
          <div className="operator-shortcuts logistics-shortcuts">
            <button
              onClick={() => {
                setFilter("pending");
                document
                  .getElementById("logistics-deliveries")
                  ?.scrollIntoView({ behavior: "instant" });
              }}
            >
              <Clock3 size={23} />
              <strong>
                {voyages.filter((v) => v.status === "HELD").length}
              </strong>
              <span>Awaiting confirmation</span>
              <ArrowRight size={15} />
            </button>
            <button onClick={() => setView("providers")}>
              <Truck size={23} />
              <strong>{pendingJobs.length}</strong>
              <span>Provider responses needed</span>
              <ArrowRight size={15} />
            </button>
            <button
              onClick={() => {
                setFilter("active");
                setView("tracking");
              }}
            >
              <Ship size={23} />
              <strong>
                {voyages.filter((v) => v.status === "CONFIRMED").length}
              </strong>
              <span>Active deliveries</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </>
      )}
      {view === "tracking" && (
        <>
          <div className="market-page-heading">
            <div>
              <span className="market-kicker">SUSTAINABLE LOGISTICS</span>
              <h1>Delivery & impact</h1>
              <p>
                Follow cargo progress and see how much freight is moving by
                water.
              </p>
            </div>
            <button
              className="button market-yellow"
              onClick={() => setView("planner")}
            >
              <Plus size={17} />
              Plan a delivery
            </button>
          </div>
          {snapshot?.impact && (
            <>
              <div className="stats-row logistics-impact">
                <Stat
                  label="Selected water tonnes"
                  value={`${snapshot.impact.selected_water_tonnes} t`}
                  note="Active commitments and completed deliveries"
                />
                <Stat
                  label="Completed water tonnes"
                  value={`${snapshot.impact.completed_water_tonnes} t`}
                  note="Recorded receipt quantities"
                />
                <Stat
                  label="Estimated CO₂ avoided"
                  value={`${snapshot.impact.estimated_full_delivery_co2_avoided_kg} kg`}
                  note="Full delivery tonne-km estimate · Synthetic factors"
                />
              </div>
              <p className="logistics-impact-note">
                <Leaf size={17} />
                Estimates include connecting trucks. Demo progress and provider
                responses are simulated.
              </p>
            </>
          )}
        </>
      )}
      {view === "providers" ? (
        <>
          <div className="market-page-heading">
            <div>
              <span className="market-kicker">TRUCKS & TERMINAL HANDLING</span>
              <h1>Confirm your delivery team</h1>
              <p>
                Record a response for each assignment. A departure can be booked
                when everyone approves.
              </p>
            </div>
            <button className="button" onClick={() => setView("overview")}>
              Back to deliveries
              <ArrowRight size={16} />
            </button>
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
          {filtered
            .filter((v) => v.status === "HELD")
            .map((v) => (
              <section className="logistics-provider-group" key={v.id}>
                <div className="logistics-provider-heading">
                  <h2>{v.vessel_name}</h2>
                  <p>
                    {date(v.departure)} · {v.weight_tonnes} t ·{" "}
                    {v.accepted_job_count}/{v.job_count} providers accepted
                  </p>
                </div>
                <ProviderJobs
                  voyage={v}
                  busy={busy}
                  act={run}
                  demo={data.demo_mode}
                />
              </section>
            ))}
          {snapshot && !filtered.some((v) => v.status === "HELD") && (
            <Empty>
              <Truck size={30} />
              <h3>No provider responses needed</h3>
              <p>
                New assignments appear when a cargo owner requests a departure.
              </p>
              <button className="button" onClick={() => setView("overview")}>
                View deliveries
              </button>
            </Empty>
          )}
        </>
      ) : (
        <section id="logistics-deliveries">
          <div className="operator-section-head">
            <div>
              <span className="market-kicker">DELIVERY MANAGEMENT</span>
              <h1>
                {view === "tracking"
                  ? "All delivery records"
                  : "Your next deliveries"}
              </h1>
              <p>Each card tells you what needs to happen next.</p>
            </div>
            <label>
              Show deliveries
              <select
                aria-label="Filter logistics deliveries"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">All deliveries</option>
                <option value="pending">Awaiting confirmation</option>
                <option value="active">Active deliveries</option>
                <option value="completed">Completed deliveries</option>
              </select>
            </label>
          </div>
          {error && (
            <div className="alert error" role="alert">
              {error}
              <button className="button" onClick={refresh}>
                Try again
              </button>
            </div>
          )}
          {!snapshot && !error && <Loading />}
          <div className="logistics-delivery-grid">
            {filtered.map((v) => (
              <LogisticsDelivery
                key={v.id}
                voyage={v}
                busy={busy}
                act={run}
                demo={data.demo_mode}
                switchRole={switchRole}
              />
            ))}
          </div>
          {snapshot && !filtered.length && (
            <div className="operator-empty">
              <Package size={32} />
              <h2>
                {search
                  ? "No deliveries match your search"
                  : "Ready for your next delivery"}
              </h2>
              <p>
                Plan a departure for entrusted cargo, or add sample records to
                explore the workflow.
              </p>
              <div className="button-row">
                {search && (
                  <button className="button" onClick={clearSearch}>
                    Clear search
                  </button>
                )}
                <button
                  className="button market-yellow"
                  onClick={() => setView("planner")}
                >
                  Plan a delivery
                  <ArrowRight size={16} />
                </button>
                {data.demo_mode && (
                  <button
                    className="button"
                    disabled={busy}
                    onClick={() =>
                      run(
                        () => api("/demo/populate", "admin", {}),
                        "Sample deliveries added. Existing records are preserved.",
                      )
                    }
                  >
                    Add demo deliveries
                  </button>
                )}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
function LogisticsDelivery({
  voyage,
  busy,
  act,
  demo,
  switchRole,
}: {
  voyage: Data;
  busy: boolean;
  act: Act;
  demo: boolean;
  switchRole?: Props["switchRole"];
}) {
  const [alternatives, setAlternatives] = useState<Data | null>(null);
  const held = voyage.status === "HELD",
    confirmed = voyage.status === "CONFIRMED";
  const active = voyage.members.filter(
    (m: Data) => !["CANCELLED", "DELIVERED"].includes(m.status),
  );
  const state =
    active[0]?.status ||
    (voyage.status === "COMPLETED" ? "DELIVERED" : voyage.status);
  const next = (
    {
      CONFIRMED: "SCHEDULED",
      SCHEDULED: "LOADING",
      LOADING: "IN_TRANSIT",
      IN_TRANSIT: "UNLOADING",
    } as Record<string, string>
  )[state];
  const ready =
    voyage.owners_ready && voyage.operator_accepted && voyage.providers_ready;
  const task = held
    ? !voyage.owners_ready
      ? "Cargo owners need to approve their quotes."
      : !voyage.operator_accepted
        ? "The boat operator needs to accept this departure."
        : !voyage.providers_ready
          ? "Confirm the truck and terminal provider responses."
          : "Everyone approved. Confirm the delivery booking."
    : state === "UNLOADING"
      ? "Record a receipt for each delivered cargo."
      : voyage.status === "COMPLETED"
        ? "Delivery complete. All cargo receipts recorded."
        : (
            {
              CONFIRMED: "Schedule this delivery to start tracking progress.",
              SCHEDULED: "Record loading when cargo is being put on the boat.",
              LOADING: "Record in transit when the boat departs.",
              IN_TRANSIT:
                "Record unloading when the boat reaches the destination.",
              DISRUPTED: "Choose a replacement boat and request fresh quotes.",
              EXPIRED: "This quote expired. Plan a new departure to continue.",
            } as Record<string, string>
          )[state] || voyage.next_action;
  const sequence = [
    "CONFIRMED",
    "SCHEDULED",
    "LOADING",
    "IN_TRANSIT",
    "UNLOADING",
    "DELIVERED",
  ];
  return (
    <article className="logistics-delivery-card" data-testid="departure">
      <div className="logistics-delivery-header">
        <div>
          <Ship size={25} />
          <div>
            <small>
              {voyage.vessel_id.startsWith("demo-market-")
                ? "SAMPLE DELIVERY"
                : "WATERWAY DELIVERY"}
            </small>
            <h2>{voyage.vessel_name}</h2>
          </div>
        </div>
        <Badge value={held ? "AWAITING_CONFIRMATION" : state} />
      </div>
      <div className="logistics-date-strip">
        <span>
          <CalendarDays size={16} />
          Departure <strong>{date(voyage.departure)}</strong>
        </span>
        <span>
          <Package size={16} />
          {voyage.weight_tonnes} tonnes · {voyage.members.length} loads
        </span>
      </div>
      {confirmed || voyage.status === "COMPLETED" ? (
        <ol className="logistics-timeline" aria-label="Delivery progress">
          {sequence.map((s, i) => (
            <li
              key={s}
              className={sequence.indexOf(state) >= i ? "complete" : ""}
              aria-current={state === s ? "step" : undefined}
            >
              <span>
                {sequence.indexOf(state) > i ? (
                  <CheckCircle2 size={15} />
                ) : (
                  i + 1
                )}
              </span>
              {title(s)}
            </li>
          ))}
        </ol>
      ) : (
        <div
          className="logistics-approvals"
          aria-label="Delivery approval checklist"
        >
          {[
            ["Cargo owners", voyage.owners_ready],
            ["Boat operator", voyage.operator_accepted],
            ["Providers", voyage.providers_ready],
          ].map(([label, complete]) => (
            <span key={label as string} className={complete ? "complete" : ""}>
              {complete ? <CheckCircle2 size={17} /> : <Clock3 size={17} />}
              {label as string}
            </span>
          ))}
        </div>
      )}
      <div className="operator-next-action">
        <CheckCircle2 size={19} />
        <p>{task}</p>
      </div>
      {held &&
        switchRole &&
        (!voyage.owners_ready || !voyage.operator_accepted) && (
          <div className="operator-handoff">
            <span>Demo · Complete the next approval</span>
            <button
              className="market-text-button"
              onClick={() =>
                switchRole(
                  voyage.owners_ready ? "operator" : "shipper",
                  voyage.vessel_id,
                )
              }
            >
              Open {voyage.owners_ready ? "boat operator" : "cargo owner"}{" "}
              workspace
              <ArrowRight size={14} />
            </button>
          </div>
        )}
      <div className="logistics-loads">
        {voyage.members.map((m: Data) => (
          <div className="logistics-load" key={m.cargo_id}>
            <div>
              <Package size={19} />
              <div>
                <h3>
                  {title(m.cargo_type)} · {m.weight_tonnes} t
                </h3>
                <p>
                  {m.origin} → {m.destination}
                </p>
                <small>Arrives by {date(m.eta)}</small>
                {m.booking_id && (
                  <small>Customer reference {m.booking_id}</small>
                )}
              </div>
            </div>
            <div className="logistics-load-price">
              <strong>{money(m.quote?.total_cost)}</strong>
              <small>
                {m.accepted ? "Owner approved" : "Awaiting owner approval"}
              </small>
              <Badge value={m.status} />
              {m.invoice && (
                <small>
                  Invoice draft {m.invoice.id}: {money(m.invoice.total)} ·{" "}
                  {m.invoice.status}
                </small>
              )}
            </div>
            {m.receipt && (
              <p className="logistics-receipt">
                <CheckCircle2 size={17} />
                {m.receipt.quantity_tonnes} t received by{" "}
                {m.receipt.receiver_name} · Simulated receipt
              </p>
            )}
            {confirmed && ["UNLOADING", "LAST_MILE"].includes(m.status) && (
              <LogisticsReceipt
                voyageId={voyage.id}
                member={m}
                act={act}
                busy={busy}
              />
            )}
          </div>
        ))}
      </div>
      {held && (
        <details className="logistics-team" open>
          <summary>
            <Truck size={17} />
            Delivery team · {voyage.accepted_job_count}/{voyage.job_count}{" "}
            responses
          </summary>
          <ProviderJobs voyage={voyage} busy={busy} act={act} demo={demo} />
        </details>
      )}
      <div className="logistics-delivery-actions">
        {held && (
          <button
            className="button market-yellow"
            disabled={busy || !ready}
            onClick={() =>
              act(
                () => api(`/lines/${voyage.id}/confirm`, "control", {}),
                "Delivery confirmed. Record the next milestone when ready.",
              )
            }
          >
            Confirm delivery bundle
            <ArrowRight size={16} />
          </button>
        )}
        {confirmed && next && (
          <button
            className="button market-yellow"
            disabled={busy}
            onClick={() =>
              act(
                () =>
                  api(`/lines/${voyage.id}/milestone`, "control", {
                    status: next,
                  }),
                "Delivery progress updated (simulated).",
              )
            }
          >
            Record {title(next)}
            <ArrowRight size={16} />
          </button>
        )}
        {voyage.status === "DISRUPTED" && (
          <button
            className="button market-yellow"
            disabled={busy}
            onClick={() =>
              act(
                async () =>
                  setAlternatives(
                    await api(
                      `/lines/${voyage.id}/recovery-options`,
                      "control",
                    ),
                  ),
                "Replacement departures checked.",
              )
            }
          >
            Find replacement departures
          </button>
        )}
      </div>
      {alternatives && (
        <div className="line-note">
          <h3>Choose a replacement departure</h3>
          {alternatives.options.map((option: Data) => (
            <div className="replacement" key={option.vessel_id}>
              <span>
                {option.vessel_name} · {date(option.departure)} ·{" "}
                {money(option.total_cost)} combined
              </span>
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  act(
                    () =>
                      api("/lines/proposals", "control", {
                        cargo_ids: option.cargo_ids,
                        vessel_id: option.vessel_id,
                        parent_id: voyage.id,
                      }),
                    "Replacement held. Fresh owner and provider approvals are required.",
                  )
                }
              >
                Request replacement quotes
              </button>
            </div>
          ))}
          {!alternatives.options.length && (
            <p>No feasible replacement available.</p>
          )}
        </div>
      )}
      <details className="logistics-record-details">
        <summary>Booking details & changes</summary>
        <p>
          Reference {voyage.id} · Version {voyage.version}
        </p>
        <p>
          Loading {date(voyage.loading_start)} · Water handover{" "}
          {date(voyage.water_end)}
        </p>
        {held && (
          <p>
            Approve before {date(voyage.cutoff)} · Quote expires{" "}
            {date(voyage.expires_at)}
          </p>
        )}
        <p>{voyage.commitment_policy}</p>
        <div className="button-row">
          {held && (
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  () => api(`/lines/${voyage.id}/cancel`, "control", {}),
                  "Proposal cancelled. Local holds released.",
                )
              }
            >
              Cancel proposal
            </button>
          )}
          {demo && confirmed && ["CONFIRMED", "SCHEDULED"].includes(state) && (
            <button
              className="button"
              disabled={busy}
              onClick={() =>
                act(
                  () => api(`/lines/${voyage.id}/disrupt`, "control", {}),
                  "Boat withdrawal simulated. Request replacement quotes.",
                )
              }
            >
              Simulate pre-pickup vessel withdrawal
            </button>
          )}
        </div>
      </details>
    </article>
  );
}
function ProviderJobs({
  voyage,
  busy,
  act,
  demo,
}: {
  voyage: Data;
  busy: boolean;
  act: Act;
  demo: boolean;
}) {
  const jobs: Data[] = [...voyage.jobs].sort(
    (a, b) =>
      a.starts_at.localeCompare(b.starts_at) || a.kind.localeCompare(b.kind),
  );
  return (
    <div className="logistics-provider-jobs">
      <p className="posting-hint">
        Provider responses are simulated in this local demo. Each response is
        saved separately.
      </p>
      {demo && jobs.some((j) => j.status === "PENDING") && (
        <button
          className="button"
          disabled={busy}
          onClick={() =>
            act(async () => {
              for (const job of jobs.filter((j) => j.status === "PENDING"))
                await api(`/lines/jobs/${job.id}/response`, "control", {
                  status: "ACCEPTED",
                });
            }, "All remaining provider responses saved individually (simulated).")
          }
        >
          Simulate remaining provider acceptances
          <CheckCircle2 size={16} />
        </button>
      )}
      <div className="logistics-job-grid">
        {jobs.map((j) => (
          <div className="logistics-job" key={j.id}>
            <div className="logistics-job-title">
              {j.kind.includes("TRUCK") ? (
                <Truck size={18} />
              ) : (
                <Package size={18} />
              )}
              <strong>{title(j.kind)}</strong>
              <Badge value={j.status} />
            </div>
            <p>
              {date(j.starts_at)}
              <br />
              to {date(j.ends_at)}
            </p>
            <details>
              <summary>Assignment details</summary>
              <small>
                {j.truck_resource_id || j.terminal_resource_id} · {j.source}
              </small>
            </details>
            {voyage.status === "HELD" && j.status === "PENDING" && demo && (
              <div className="button-row">
                <button
                  className="button small"
                  aria-label={`Simulate accept ${title(j.kind)} ${j.id}`}
                  disabled={busy}
                  onClick={() =>
                    act(
                      () =>
                        api(`/lines/jobs/${j.id}/response`, "control", {
                          status: "ACCEPTED",
                        }),
                      "Provider acceptance recorded (simulated).",
                    )
                  }
                >
                  Accept
                </button>
                <button
                  className="button small"
                  aria-label={`Simulate decline ${title(j.kind)} ${j.id}`}
                  disabled={busy}
                  onClick={() =>
                    act(
                      () =>
                        api(`/lines/jobs/${j.id}/response`, "control", {
                          status: "DECLINED",
                        }),
                      "Provider declined. Local proposal allocations released.",
                    )
                  }
                >
                  Decline
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
function LogisticsReceipt({
  voyageId,
  member,
  act,
  busy,
}: {
  voyageId: string;
  member: Data;
  act: Act;
  busy: boolean;
}) {
  const [name, setName] = useState(""),
    [quantity, setQuantity] = useState(String(member.weight_tonnes));
  return (
    <form
      className="logistics-receipt-form"
      onSubmit={(e) => {
        e.preventDefault();
        void act(
          () =>
            api(`/lines/${voyageId}/receipt`, "control", {
              cargo_id: member.cargo_id,
              quantity_tonnes: Number(quantity),
              receiver_name: name,
            }),
          "Cargo delivery receipt saved (simulated).",
        );
      }}
    >
      <label>
        Receiver name
        <input
          aria-label={`Receiver name ${member.cargo_id}`}
          required
          minLength={2}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label>
        Received tonnes
        <input
          aria-label={`Received tonnes ${member.cargo_id}`}
          type="number"
          required
          min="0.001"
          max={member.weight_tonnes}
          step="0.001"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
      </label>
      <button
        className="button market-yellow"
        disabled={busy || name.trim().length < 2}
      >
        Record door receipt
        <CheckCircle2 size={16} />
      </button>
    </form>
  );
}
