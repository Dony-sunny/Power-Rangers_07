# Data provenance

Reviewed 7 October 2026. **No live navigation, tariff, traffic, government, weather or GPS feed is connected.** All operational numeric fields used by the prototype are simulated.

| Data | Classification | Source / verification |
|---|---|---|
| NW-3 corridor context and approximately 205 km historic principal system | Source-grounded context | [IWAI NW-3 overview](https://www.iwai.gov.in/offerings/national-waterway/national-waterways3?page=0). The app models only the Maradu–Alappuzha demo subset, not the whole declared network. |
| Maradu, Vaikom, Thanneermukkom, Alappuzha terminal names | Source-grounded names | [IWAI terminal list](https://iwai.gov.in/offerings/national-waterway/national-waterways3?page=1); names are used as demo anchors, not confirmation of current bookable capacity. |
| Tidal variation and Thanneermukkom/Thrikunnapuzha lock context | Source-grounded context | IWAI overview above. Live tide, lock and navigation observations are not fetched. |
| Nodes, terminal coordinates and polygon/map geometry | Approximate prototype values | Hand-authored geographic anchors and schematic shapes. Not surveyed route geometry. OSM tiles are optional context only. |
| Three segment distances 28 / 12 / 24 km | Synthetic | Total 64 km demonstration graph; not an official measured voyage distance. |
| Depths 2.4 / 2.0 / 2.2 m, clearance, width, lock hours | Synthetic safety fixtures | `source_name=Synthetic hackathon fixture`, `source_date=2026-10-06`, `verification_status=SIMULATED`, `last_verified=null`, confidence=DEMO. Never use for real navigation. |
| Terminal capacities, storage, approach depths, equipment, handling tariffs, wait | Synthetic | Terminal records identify grounded names separately from synthetic capabilities; source dates and verification labels are stored. |
| Vessels, dimensions, registration/insurance, reliability and historical counts | Synthetic | Fictional vessels/operators and simulated platform verification. No official certificate validation is performed. |
| Cargo, quoted costs, scheduled service, availability | Synthetic input + computed output | Seed fixture requests and configurable rate assumptions. Quotes, pool membership, booking totals and capacity are calculated by code. |
| Road distance, speeds, handling and turnaround | Prototype assumptions | Haversine × 1.35; road 32 km/h, water 10 km/h; handling 0.75 h; backhaul turnaround 1 h. |
| Emissions | Prototype assumptions | Road 0.105 kg CO₂/t-km; water 0.028 kg CO₂/t-km. No certified source/calibration. Source metadata is exposed in the API. |
| Truck trips avoided | Prototype estimate | Ceiling of shifted tonnes / 20 t per cargo. Equivalent long-haul road movements; connecting truck legs still exist. Not a count of trucks removed from roads. |
| Demand heatmap, gap/activation score, modal suitability | Demo-derived decision support | Aggregated actual application requests/bookings using synthetic inputs. No official planning authority or forecast accuracy. |
| Tracking | Simulated | Waypoint interpolation advances with actual shipment-state changes; all TrackingEvent records mark `simulated=true`. |
| Operator navigation reports | Unverified user observations | Reporter, location, type, timestamp, confidence and 24-hour expiry stored. These do not automatically become official restrictions. |

For NW-3 scope, IWAI describes the historic 205 km system; legal extensions and wider network definitions are outside this prototype. The project does not claim to model the full present legal extent. The user-supplied hackathon context and internal engineering weights were not treated as a verified numerical judging rubric.

Every real deployment needs verified vessel records, hydrographic/clearance data, terminal surveys, legal review and authorized operational sources. A demo PASS means only **PASS against the configured synthetic values**. No authority data is fabricated.
