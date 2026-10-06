# Three-minute demo

Before judging: install dependencies, start with `python scripts/dev.py`, generate sample upload files, reset through Platform admin, check microphone permission only if using recording, and rehearse the transcript fallback. Keep default offline map enabled. No API credential is required.

| Time | Action | Explain |
|---|---|---|
| 0:00–0:20 | Operator → Voice availability → Use demo transcript → review and confirm | “A traditional operator can provide Malayalam or transliterated speech. We disclose the offline transcript fallback and confirm exact availability times.” |
| 0:20–0:40 | Shipper → New cargo request → describe or upload sample PDF → Extract & review | “Demand becomes validated structured data. Missing information stays missing until the shipper confirms it.” Use the preloaded hero request for the timed plan if creating a duplicate. |
| 0:40–1:00 | Hero cargo → matching → expand Deep Blue | “This cheaper candidate looks commercially strong but fails draft. The model cannot override a physical constraint.” |
| 1:00–1:20 | Inspect road / water / hybrid and charges | “We compare the whole delivered cost, including trucks and both terminals. Urgency can make road the correct choice.” |
| 1:20–1:40 | Optimize | “OR-Tools selects 80 + 58 tonnes: 138 tonnes on 150 tonnes of capacity, 92% utilization. The inputs are fixtures; the result is calculated.” |
| 1:40–1:55 | Find return | “62 tonnes of coir fits a verified demo return window. A suggestion is not yet an avoided empty trip.” |
| 1:55–2:15 | Confirm pooled hybrid booking → Manifest | “Bookings, shipments, berth reservations, invoice drafts and impact records persist together. This is a prototype manifest package.” |
| 2:15–2:35 | Dispatch: advance milestones, or show an independent recovery scenario | For recovery, use an individual booking after reset: cancellation → replacement/road alternatives → explicit approval. Pooled loads require individual recovery approvals. |
| 2:35–2:55 | Government analytics | “Selected tonnes, equivalent truck movements, estimated savings and CO₂ are derived from these actual demo bookings. Completed impact is separate. Unserved demand shows where the network has gaps.” |
| 2:55–3:00 | Close | “Jalayatra connects freight understanding, physical feasibility, utilization optimization and execution into one waterway operating system.” |

## Independent deterministic scenarios

Switch to Platform admin; reset before each independent scenario.

- **A:** Normal confirmed shipment. Switch to dispatch to advance states.
- **B:** Commercially attractive Deep Blue rejected for draft. All other results come from the same constraint engine.
- **C:** Calculate pool. Switch to shipper and click Optimize again to obtain a scoped preview, then confirm pooled booking.
- **D:** Return-load search; no impact is counted merely from this preview.
- **E:** Create/identify hero booking, withdraw vessel availability and return alternatives. Dispatch reviews and approves recovery.
- **F:** Toggle simulated flood. Road comparison becomes unavailable, unbooked cargo becomes critical, policy dashboard labels the simulation. Reset or toggle again to restore.

Use scheduled services on a fresh reset to book the 58 t terminal-to-terminal steel request on the Periyar shared service. Service capacity is enforced per segment. The CSV preview uses CargoRequest field-name headers.

## Failure recovery during a live presentation

If LLM/STT fails, select the disclosed demo transcript or type the supported sample. If tile internet fails, the local schematic remains visible. If a stale booking blocks a scenario, reset the demo, then repeat. If an upload has no text, show missing fields and enter them manually. Never hide the source label or claim fixture values are live.
