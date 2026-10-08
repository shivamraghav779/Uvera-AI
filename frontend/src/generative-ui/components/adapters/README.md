# Framework adapters

An adapter maps the platform's semantic components to one UI framework. It is a
`FrameworkAdapter` (see `types.ts`): an id plus presentational React components
that receive already-resolved view props.

| Directory   | Status      | Notes |
| ----------- | ----------- | ----- |
| `shadcn/`   | implemented | Default. Complete: implements every semantic component. |
| `material/` | implemented | Partial: core controls and surfaces; the rest falls back to the default adapter. In-house, does not wrap `@mui/material`. |
| mui, mantine, react-aria, aceternity | planned | Listed by the backend's framework registry as `planned`; selecting them is rejected until an adapter is registered here. |

## Adding a framework

1. Create `<framework>/index.ts(x)` exporting a `FrameworkAdapter`. Implement as
   many `AdapterComponents` as you like; missing ones fall back to the default.
2. Register it in `registry/frameworkRegistry.ts`.
3. Mark the same id `available` in the backend's `design_registry.py`.

Nothing else changes: not the UI schema, not the mutation engine, not the prompts.
Adapters must style only through the `--g-*` theme variables so themes keep working.
