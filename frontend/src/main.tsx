import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";

import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
// Type families a generated UI can choose from (theme.typography.font / heading_font).
import "@fontsource-variable/fraunces";
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/plus-jakarta-sans";
import "@fontsource-variable/nunito";

import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
