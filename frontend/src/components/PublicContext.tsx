import { useEffect, useState } from "react";
import { api, date, type Data, title } from "../api";
import { Badge, Loading, Panel, Stat } from "./UI";

export default function PublicContext({ role }: { role: string }) {
  const [context, setContext] = useState<Data | null>(null);
  const [location, setLocation] = useState("maradu");
  const [weather, setWeather] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true;
    api("/corridor-context", role)
      .then((result) => active && setContext(result))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [role]);
  useEffect(() => {
    let active = true;
    setWeather(null);
    setError("");
    api(`/corridor-context/weather?location=${location}`, role)
      .then((result) => active && setWeather(result))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [role, location, refresh]);
  return (
    <>
      <Panel title="Waterway reference" eyebrow="PUBLISHED PUBLIC INFORMATION">
        {context ? (
          <div className="role-intro">
            <p>{context.description}</p>
            <p>
              Published terminal references: {context.terminals.join(" · ")}.
            </p>
            <p>{context.limitations}</p>
            <p>
              <a href={context.source.url} target="_blank" rel="noreferrer">
                {context.source.name}
              </a>{" "}
              · Checked {context.source.checked_on}
            </p>
          </div>
        ) : (
          <Loading />
        )}
      </Panel>
      <Panel
        title="Corridor weather"
        eyebrow="EXTERNAL WEATHER MODEL"
        action={
          <button
            className="button"
            disabled={!weather && !error}
            onClick={() => setRefresh((old) => old + 1)}
          >
            Refresh weather
          </button>
        }
      >
        <div className="form-content">
          <label className="field">
            Location
            <select
              aria-label="Weather location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            >
              {context?.locations.map((item: Data) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {error && <p role="alert">{error}</p>}
        {!weather && !error && <Loading />}
        {weather && (
          <>
            <div className="role-intro">
              <Badge value={weather.status} />
              <p>{weather.message}</p>
            </div>
            {weather.values && (
              <div className="stats-row">
                {Object.entries(weather.values).map(([key, value]) => (
                  <Stat
                    key={key}
                    label={title(key)}
                    value={`${value} ${weather.units[key]}`}
                  />
                ))}
              </div>
            )}
            <div className="role-intro">
              <p>
                Model time {date(weather.model_time)} · Retrieved{" "}
                {date(weather.fetched_at)}
              </p>
              <p>{weather.limitations}</p>
              <a
                href={weather.source.documentation}
                target="_blank"
                rel="noreferrer"
              >
                Weather data by Open-Meteo
              </a>
              <p>{weather.source.license}</p>
            </div>
          </>
        )}
      </Panel>
    </>
  );
}
