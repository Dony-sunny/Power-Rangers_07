import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./readability.css";
import "./continuation.css";
import "./cargo-lines.css";
import "./simple-ui.css";
import "./marketplace.css";
import "./operator-marketplace.css";
import "./logistics-marketplace.css";
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
