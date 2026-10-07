export type TeamRole = {
  id: string;
  label: string;
  description: string;
  tools: { id: string; label: string }[];
};

export const workspaceGroups: Record<string, TeamRole[]> = {
  shipper: [
    {
      id: "shipper",
      label: "Shipper procurement",
      description: "Review cargo, compare freight and plan recurring capacity.",
      tools: [
        { id: "intake", label: "Text, documents & bulk import" },
        { id: "matching", label: "Matching, pooling & backhaul" },
        { id: "services", label: "Recurring services & contracts" },
        { id: "evidence", label: "Photos, labels & documents" },
      ],
    },
    {
      id: "dispatch",
      label: "Shipper dispatch",
      description:
        "Follow your deliveries, coordinate pickup and handle exceptions.",
      tools: [
        { id: "tracking", label: "Delivery tracking" },
        { id: "appointments", label: "Truck appointments" },
        { id: "evidence", label: "Handover evidence" },
      ],
    },
    {
      id: "warehouse",
      label: "Warehouse",
      description:
        "Verify the accepted load, packing, loading order and gate out.",
      tools: [
        { id: "overview", label: "Loading & handover" },
        { id: "evidence", label: "Photos, QR labels & loading sheets" },
      ],
    },
    {
      id: "receiver",
      label: "Consignee",
      description:
        "Record received quantities and verify delivery with a local demo code.",
      tools: [
        { id: "overview", label: "Incoming loads & receipts" },
        { id: "evidence", label: "Delivery verification & photos" },
      ],
    },
    {
      id: "finance",
      label: "Seller finance",
      description:
        "Review your organization's invoice drafts, payments and disputes.",
      tools: [{ id: "finance", label: "Invoices, payments & disputes" }],
    },
  ],
  operator: [
    {
      id: "operator",
      label: "Vessel operator",
      description:
        "Plan dated services and review corridor performance for your fleet.",
      tools: [
        { id: "services", label: "Recurring departures" },
        { id: "intelligence", label: "Corridor history" },
        { id: "reports", label: "Navigation observations" },
        { id: "finance", label: "Own payments & settlements" },
      ],
    },
    {
      id: "fleet",
      label: "Fleet dispatcher",
      description: "Assign compatible demand to vessels and coordinate crew.",
      tools: [
        { id: "optimization", label: "Fleet optimization" },
        { id: "fleet", label: "Fleet & crew" },
        { id: "services", label: "Dated service calendar" },
        { id: "tracking", label: "Shared departures" },
      ],
    },
    {
      id: "captain",
      label: "Captain",
      description:
        "Read the approved route, record shared milestones and report hazards.",
      tools: [
        { id: "tracking", label: "Voyages & route tracking" },
        { id: "reports", label: "Navigation observations" },
        { id: "evidence", label: "Voyage evidence" },
      ],
    },
    {
      id: "maintenance",
      label: "Maintenance",
      description:
        "Record defects, inspections and verified return to service.",
      tools: [{ id: "overview", label: "Defects & inspections" }],
    },
  ],
  control: [
    {
      id: "control",
      label: "Logistics coordinator",
      description:
        "Optimize authorized cargo and coordinate common operating resources.",
      tools: [
        { id: "tracking", label: "Delivery tracking & exceptions" },
        { id: "optimization", label: "Fleet optimization" },
        { id: "services", label: "Recurring services" },
        { id: "resources", label: "Terminal resources & appointments" },
        { id: "intelligence", label: "Operational intelligence" },
        { id: "evidence", label: "Delivery evidence" },
      ],
    },
    {
      id: "terminal",
      label: "Terminal operator",
      description:
        "Manage your berths, equipment, gate appointments and handling records.",
      tools: [
        { id: "overview", label: "Handling operations" },
        { id: "resources", label: "Resource calendar & truck gates" },
        { id: "tracking", label: "Loading & unloading milestones" },
        { id: "evidence", label: "Handling evidence" },
      ],
    },
    {
      id: "compliance",
      label: "Compliance & safety",
      description: "Review certificates and the audit trail.",
      tools: [{ id: "overview", label: "Certificates & audit" }],
    },
    {
      id: "network",
      label: "Waterway control",
      description:
        "Review navigation observations and operational corridor evidence.",
      tools: [
        { id: "reports", label: "Review navigation reports" },
        { id: "intelligence", label: "Corridor intelligence" },
      ],
    },
    {
      id: "government",
      label: "Government analytics",
      description:
        "Existing analysis workspace; integration point for your teammate's government work.",
      tools: [{ id: "overview", label: "Government analysis" }],
    },
    {
      id: "admin",
      label: "Platform admin",
      description:
        "Manage stored identities, provider diagnostics and presentation settings.",
      tools: [
        { id: "administration", label: "Organizations, users & providers" },
        { id: "finance", label: "Finance & disputes" },
        { id: "audit", label: "Audit trail" },
        { id: "demo", label: "Demo settings" },
        { id: "judge", label: "Guided judge walkthrough" },
      ],
    },
  ],
};

export function groupForRole(role: string) {
  return (
    Object.keys(workspaceGroups).find((key) =>
      workspaceGroups[key].some((team) => team.id === role),
    ) || "shipper"
  );
}
