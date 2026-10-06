import {
  MapContainer,
  Polyline,
  CircleMarker,
  Tooltip,
  Polygon,
  TileLayer,
  useMap,
} from "react-leaflet";
import { useEffect, useState } from "react";
import type { LatLngExpression } from "leaflet";
import type { Data } from "../api";
import "leaflet/dist/leaflet.css";

function ResizeMap() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => map.invalidateSize(), 100);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}
const coast: LatLngExpression[] = [
  [10.2, 76.1],
  [9.98, 76.22],
  [9.9, 76.27],
  [9.77, 76.28],
  [9.66, 76.3],
  [9.47, 76.3],
  [9.3, 76.37],
  [9.3, 76.7],
  [10.2, 76.7],
];
const lake: LatLngExpression[] = [
  [9.94, 76.3],
  [9.85, 76.33],
  [9.76, 76.35],
  [9.67, 76.38],
  [9.61, 76.34],
  [9.51, 76.34],
  [9.54, 76.37],
  [9.62, 76.43],
  [9.75, 76.42],
  [9.88, 76.36],
];
export default function RouteMap({
  data,
  heat = false,
}: {
  data: Data;
  heat?: boolean;
}) {
  const [online, setOnline] = useState(false);
  const nodes: Data[] = data.nodes || [];
  return (
    <div className="route-map">
      <MapContainer
        center={[9.74, 76.36]}
        zoom={9}
        zoomControl={false}
        scrollWheelZoom={false}
        attributionControl={false}
      >
        <Polygon
          positions={coast}
          pathOptions={{
            fillColor: "#edf0e8",
            fillOpacity: 1,
            color: "#d4e0d6",
            weight: 1,
          }}
        />
        <Polygon
          positions={lake}
          pathOptions={{
            fillColor: "#d8e9e8",
            fillOpacity: 1,
            color: "#c2dcd8",
            weight: 1,
          }}
        />
        {online && (
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            eventHandlers={{ tileerror: () => setOnline(false) }}
          />
        )}
        {heat &&
          nodes.map((n) => (
            <CircleMarker
              key={`heat-${n.id}`}
              center={[n.latitude, n.longitude]}
              radius={
                20 +
                Math.min(
                  25,
                  (data.cargo || [])
                    .filter(
                      (c: Data) =>
                        c.origin.toLowerCase().includes(n.id) ||
                        (n.id === "maradu" &&
                          ["Kochi", "Kalamassery"].includes(c.origin)),
                    )
                    .reduce((s: number, c: Data) => s + c.weight_tonnes, 0) / 8,
                )
              }
              pathOptions={{
                weight: 0,
                fillColor: "#f5b05d",
                fillOpacity: 0.28,
              }}
            />
          ))}
        <Polyline
          positions={nodes.map((n) => [n.latitude, n.longitude])}
          pathOptions={{ color: "#fff", weight: 8 }}
        />
        <Polyline
          positions={nodes.map((n) => [n.latitude, n.longitude])}
          pathOptions={{ color: "#287866", weight: 3, dashArray: "7 7" }}
        />
        {nodes.map((n, i) => (
          <CircleMarker
            key={n.id}
            center={[n.latitude, n.longitude]}
            radius={i === 0 || i === nodes.length - 1 ? 7 : 4}
            pathOptions={{
              color: "#fff",
              weight: 3,
              fillColor: "#277664",
              fillOpacity: 1,
            }}
          >
            <Tooltip
              permanent
              direction="right"
              className="map-label"
              offset={[10, 0]}
            >
              {n.name}
              <small>
                {i === 0
                  ? "ORIGIN TERMINAL"
                  : i === nodes.length - 1
                    ? "DESTINATION"
                    : "NW-3 WAYPOINT"}
              </small>
            </Tooltip>
          </CircleMarker>
        ))}
        {(data.shipments || []).map((s: Data) => (
          <CircleMarker
            key={s.shipment.id}
            center={[s.shipment.latitude, s.shipment.longitude]}
            radius={8}
            pathOptions={{
              color: "#fff",
              weight: 3,
              fillColor: "#df954a",
              fillOpacity: 1,
            }}
          >
            <Tooltip>
              {s.vessel_name} · {s.shipment.status}
            </Tooltip>
          </CircleMarker>
        ))}
        <ResizeMap />
      </MapContainer>
      <div className="map-controls">
        <span className="map-chip">
          <i />
          NW-3 corridor
        </span>
        <button onClick={() => setOnline(!online)}>
          {online ? "Use offline map" : "OSM basemap"}
        </button>
      </div>
      <div className="map-note">
        {online ? (
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noreferrer"
          >
            © OpenStreetMap contributors
          </a>
        ) : (
          "Offline schematic · approximate geography"
        )}
        <span>Depths & positions are simulated</span>
      </div>
    </div>
  );
}
