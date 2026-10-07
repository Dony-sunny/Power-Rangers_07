# AI and optimization

## Actual AI boundary

With a configured compatible LLM, `intelligence/provider/llm.py` supports structured cargo/voice extraction, image-document requests and model-selected function calls. `broker_agent/agent.py` bounds the tools and number of turns; server-owned cargo scope cannot be changed by model arguments. LLM responses are schema-validated. Extracted missing values stay null and require user confirmation.

Without credentials, local regex/normalization rules and a deterministic tool sequence keep the demo working. The UI labels this **deterministic local extraction**, not AI/ML. Native Malayalam place names/suffixes and the provided transliteration are supported; this is a narrow sample parser, not a measured multilingual model. Audio fallback is an explicitly chosen sample transcript, never silently represented as transcription of a user's audio.

Provider failure or invalid JSON returns to local extraction. Text PDFs use pypdf in a bounded worker; scanned PDF/PNG/JPEG use actual local RapidOCR ONNX recognition after safe validation/rendering. OCR recognition confidence is not calibrated cargo accuracy. If recognition fails, an optional image-capable provider can assist; otherwise fields stay missing. No real external LLM/STT credentials were available. [Provider setup](PROVIDER_SETUP.md) documents adapters, diagnostics and smoke validation. No fake training data or weather-as-ML claim exists.

## Deterministic services

- Dijkstra filters graph edges for depth plus 0.2 m under-keel margin, air draft, conservative two-beam width, closures and restrictions.
- Vessel/cargo rules reject overweight/volume excess, incompatible categories, unapproved dangerous goods, missing cold-chain equipment, maintenance and certificate failures.
- Terminal checks include jetty length, approach depth, storage, covered handling, crane/forklift and road access. Configurable berth/equipment/storage/gate resources enforce peak overlap and bounded alternate-slot search; handling duration remains a disclosed fixed assumption.
- Lock opening hours add disclosed waiting. Certificates must remain valid through calculated voyage completion.
- Terminal selection evaluates valid origin/destination combinations along a vessel's listed corridor, connecting-road distance, handling, waiting, route and SLA. Road distances use a disclosed straight-line × 1.35 approximation, not a road-routing API.
- Delivered costs are sums of configured rate lines. Carbon uses tonne-km factors. Modes missing SLA/constraints cannot win; urgent requests can select road.
- Matching profiles are configurable engineering weights, not official judge weights or scientifically calibrated rankings. Capacity score includes a disclosed greedy pooling potential estimate; final pool membership is solved separately.
- Backhaul checks an actual reverse availability listing, capacity, readiness, route, completion window and prototype one-hour turnaround.
- Scheduled capacity enforces tonnes across each traversed service segment and revalidates cargo compatibility/volume.
- Impact aggregates actual active application booking records; delivered tonnes are separately reported. Cancellation/replanning does not count as confirmed impact.

## OR-Tools formulation

Each eligible cargo has a binary variable. The anchor load is forced in. Weight and volume are rounded **up** to integer units; capacities round **down**. Constraints bound total weight/volume, reject pairwise incompatible cargo and incompatible synchronized deadlines, and restrict loads to a common terminal corridor. The objective prioritizes compatible tonnage, then estimated freight revenue, then fewer handling operations. Route deviation is zero in this prototype's common-terminal pool.

CP-SAT uses one worker, fixed random seed and a two-second limit. OPTIMAL/FEASIBLE are disclosed; other statuses do not return an invented answer. Selected cargo undergoes combined feasibility again at booking, including synchronized arrival. Google documents CP-SAT's integer formulation and solution-status semantics in [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver).

## Explainability and limitations

Recommendations expose PASS/FAIL reasons, score factors/weights, cost lines, ETA/SLA, emission factors and source type. Heuristic confidence labels are not calibrated model accuracy. Synthetic rate history is separate from actual app milestone statistics, and small samples show insufficient history. Booking risk and activation scores are transparent decision-support rules. Learned ETA, multi-tour VRP and authoritative traffic/weather integration remain roadmap.

## Fleet assignment and recurring capacity

The fleet solver assigns binary cargo/vessel pairs after individual feasibility, then enforces weight, volume, pair compatibility and common voyage windows. Combined feasibility adds bounded lazy cuts if necessary. It first rewards served tonnage, then applies BALANCED/MIN_COST/MAX_UTILIZATION/MIN_EMPTY/ON_TIME. Repositioning adds graph travel/readiness; before/after cost, utilization, empty distance and unmatched cargo are visible. One worker and a total three-second budget yield OPTIMAL/FEASIBLE or an honest no-result status. This is one voyage per vessel, not general multi-tour VRP; cost estimates conservatively sum cargo plans.

Recurring patterns generate concrete dated departures. Segment capacities and contract holds are deterministic, and approved draws apply agreed water-freight rates. Recovery offers revalidated alternatives for eight pre-departure disruption types, ranks SLA/cost/ETA/reliability/carbon and can approve a complete pool atomically. Neither scheduling nor recovery depends on LLM arithmetic.
