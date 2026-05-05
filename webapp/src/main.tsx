import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

const rootEl = document.getElementById("root");
if (!rootEl) {
  document.body.innerHTML = '<div style="color:red;padding:2rem;">Error: #root element not found</div>';
} else {
  createRoot(rootEl).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
