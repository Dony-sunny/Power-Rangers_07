# Provider setup and offline fallback

The complete demo runs with `AI_PROVIDER=local`, `STT_PROVIDER=auto`, `TRACKING_PROVIDER=demo` and `WEATHER_PROVIDER=demo`. Local extraction is deterministic. Local ONNX OCR performs actual image recognition without a network request after installation. The audio fallback uses a disclosed sample transcript.

## Optional language model

Copy `.env.example` to the ignored `.env`; set `AI_PROVIDER=external`, `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY`. The adapter appends `/chat/completions` to the base URL. The provider must support chat-completions messages, JSON response mode and tool calls; image extraction additionally requires image input. Restart the backend after changing configuration.

Run `.venv/Scripts/python.exe scripts/provider_smoke.py`, or open Platform admin → Users & providers → Run AI connection check. A successful schema-validated response is required for Connected. Configuration alone does not establish a connection. No LLM credential was available for this implementation run; mocked HTTP tests cover valid responses, malformed JSON, outages and safe transient retries.

`PROVIDER_TIMEOUT_SECONDS=8` bounds each HTTP request. Only read-only LLM requests retry once for 429/502/503/504. Broker orchestration has a 16-second external budget and bounded tool turns. Failure returns to disclosed local extraction/tool execution. Every extraction still requires schema validation and user confirmation.

## Malayalam speech

Set `STT_PROVIDER=external`, `STT_URL` and `STT_API_KEY`. The endpoint receives multipart `file` plus `language=ml` and a Bearer authorization header, and must return `{"text":"transcribed Malayalam or mixed-language text"}`. Upload real audio or use browser microphone recording in Voice availability. A nonempty validated transcription produces LIVE SPEECH. Speech is never retried implicitly. Invalid/failed transcription shows an error; choose Use demo transcript explicitly to continue.

The local parser supports the supplied utterance, alternate English/transliterated Malayalam phrases and native Malayalam place forms. It does not infer an unknown destination. Exact availability times and registered vessel identity require operator confirmation. No real speech credential/audio-provider evaluation was performed here; do not claim measured Malayalam accuracy.

## Optional position and weather feeds

Set `TRACKING_PROVIDER=external`, `TRACKING_URL`, `TRACKING_API_KEY`. GET includes `vessel_id`; the response is `{vessel_id,latitude,longitude,speed,heading,timestamp}`. Speed is in km/h and heading in degrees. Timestamps need timezone offsets and must be within 15 minutes; a mismatched vessel or invalid position triggers simulated fallback.

Set `WEATHER_PROVIDER=external`, `WEATHER_URL`, `WEATHER_API_KEY`. GET includes latitude/longitude; response is `{location:[latitude,longitude],rainfall,wind,warning_level,timestamp}`. Adapter contract uses rainfall in mm and wind in km/h; warning level is NONE/ADVISORY/HIGH/SEVERE. Values need timezone-aware freshness within one hour and location proximity. Failure is disclosed simulated weather. These adapters do not change approved route safety or booking constraints. Authoritative safety integration requires a separately reviewed rule and trusted source.

Authorized endpoints: `/api/providers/tracking/{vessel_id}` and `/api/providers/weather`. The existing shipment map remains simulated; external adapters are optional read endpoints, not a claim of AIS/IMD integration. Diagnostics exposes configuration/status only, never keys.

## Future commerce and identity

`backend/services/connectors.py` defines payment, insurance, government-document and identity contracts. Defaults return Prototype / Not connected. Payment states move no funds; government packages are ready-data exports. OIDC/OAuth2/enterprise SSO must verify issuer, audience, signature and expiry, map subjects to stored users, and apply stored roles/disabled status. See [Security](SECURITY.md) and [PostgreSQL migration](POSTGRESQL_MIGRATION.md).
