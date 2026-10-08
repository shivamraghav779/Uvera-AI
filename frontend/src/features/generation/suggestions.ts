/** Ideas offered when a workspace is empty: whole products, and single views of the demo data. */
export const STARTER_PROMPTS = [
  "Build me a modern AI recruitment SaaS.",
  "Create a premium website for an architecture studio.",
  "Build a modern AI productivity app for small teams.",
  "Create a sales dashboard with revenue, orders and monthly sales.",
] as const;

/** Follow-ups offered once a single view exists. */
export const EDIT_PROMPTS = [
  "Make it dark",
  "Put the chart above the table",
  "Add a region filter",
  "Use a more compact design",
  "Undo the last change",
] as const;

/** Follow-ups for an application: one screen, the whole product, or its history. */
export const APPLICATION_PROMPTS = [
  "Redesign this screen",
  "Make the entire application more premium",
  "Add a settings screen",
  "Switch to a dark look",
  "Go back to the original version",
] as const;

/** Follow-ups that make sense for a selected component. */
export const SELECTION_PROMPTS = ["Make this half width", "Move this to the top", "Remove this"] as const;
