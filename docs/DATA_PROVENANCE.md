# Data provenance

Operational cargo, vessels, availability, channel conditions, rates, provider responses and positions are prototype fixtures. Quote arithmetic and persisted workflow transitions are real application behavior using those fixtures. Money is not transferred and trucks or boats are not dispatched.

The read-only corridor reference cites [IWAI's NW3 overview](https://www.iwai.gov.in/offerings/national-waterway/national-waterways3), checked on 7 October 2026. Its described original canal system includes the 168 km Kottapuram–Kollam West Coast Canal, 23 km Udyogmandal Canal and 14 km Champakara Canal. This is not presented as the full extended statutory length. Published terminal names do not establish present access, depth or availability.

Weather is fetched from [Open-Meteo's documented forecast API](https://open-meteo.com/en/docs) for four fixed approximate corridor locations. Displayed values are weather-model output, not station measurements, official flood warnings, AIS or waterway clearance. The source, model time, retrieval time and CURRENT_MODEL/CACHED/UNAVAILABLE state are visible. Units, coordinates, finite values and model freshness are validated. Successful results are cached in memory for five minutes; requests have a five-second timeout, one in-flight request per location and a one-minute retry cooldown. A validated older result can be displayed with its timestamp for at most 90 minutes of model age. No synthetic fallback weather is substituted. Cache is lost on server restart.

The free Open-Meteo endpoint is used for this non-commercial prototype, with attribution and CC BY 4.0 labeling. A commercial deployment must review its [current terms](https://open-meteo.com/en/terms) and provision an appropriate service agreement.

Public weather never changes booking constraints, safety checks, resource assignments or government analytics. The existing optional configured provider adapters retain their own clearly disclosed fallback behavior.
