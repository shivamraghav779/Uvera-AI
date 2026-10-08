import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/Badge";
import { Field, SelectInput } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Segmented";
import {
  findCapabilityGaps,
  frontendCapabilities,
  hasGaps,
  usableFrameworkIds,
} from "@/generative-ui/registry/capabilityRegistry";
import { implementedComponents } from "@/generative-ui/registry/frameworkRegistry";
import { API_BASE_URL } from "@/services/api/client";
import { usePreferencesStore, type ChromeTheme } from "@/stores/preferencesStore";

import { useCapabilities, useFrameworkCatalog, useThemeCatalog } from "../workspace/queries";

import { DataSourcesCard } from "./DataSourcesCard";

function Card({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-app-border bg-app-panel p-5">
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-0.5 mb-4 text-sm text-app-muted">{description}</p>
      {children}
    </section>
  );
}

export function SettingsPage() {
  const preferences = usePreferencesStore();
  const themes = useThemeCatalog();
  const frameworks = useFrameworkCatalog();
  const capabilities = useCapabilities();

  const frontend = frontendCapabilities();
  const gaps = capabilities.data ? findCapabilityGaps(capabilities.data, frameworks.data) : null;
  const usable = usableFrameworkIds(frameworks.data);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight">Settings</h1>

        <Card title="Appearance" description="How this application looks. Generated UIs have their own themes.">
          <Segmented<ChromeTheme>
            label="Application theme"
            value={preferences.chromeTheme}
            onChange={preferences.setChromeTheme}
            options={[
              { value: "light", label: "Light" },
              { value: "dark", label: "Dark" },
            ]}
          />
        </Card>

        <Card
          title="New workspaces"
          description="The look the first generated UI of a workspace starts with. With Auto, each new UI gets a palette picked for it unless you name colours in your request. It can be changed at any time."
        >
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Theme">
              {(id) => (
                <SelectInput
                  id={id}
                  value={preferences.newWorkspaceThemePreset}
                  onChange={(e) => preferences.setNewWorkspaceLook({ newWorkspaceThemePreset: e.target.value })}
                >
                  <option value="">Auto (picked for you)</option>
                  {themes.data?.presets.map((preset) => (
                    <option key={preset.id} value={preset.id}>
                      {preset.name}
                    </option>
                  ))}
                </SelectInput>
              )}
            </Field>
            <Field label="Design system">
              {(id) => (
                <SelectInput
                  id={id}
                  value={preferences.newWorkspaceDesignSystem}
                  onChange={(e) => preferences.setNewWorkspaceLook({ newWorkspaceDesignSystem: e.target.value })}
                >
                  <option value="">Default</option>
                  {frameworks.data?.design_systems.map((system) => (
                    <option key={system.id} value={system.id}>
                      {system.name}
                    </option>
                  ))}
                </SelectInput>
              )}
            </Field>
            <Field label="Component framework">
              {(id) => (
                <SelectInput
                  id={id}
                  value={preferences.newWorkspaceFramework}
                  onChange={(e) => preferences.setNewWorkspaceLook({ newWorkspaceFramework: e.target.value })}
                >
                  <option value="">Default</option>
                  {frameworks.data?.frameworks
                    .filter((framework) => usable.includes(framework.id))
                    .map((framework) => (
                      <option key={framework.id} value={framework.id}>
                        {framework.name}
                      </option>
                    ))}
                </SelectInput>
              )}
            </Field>
          </div>
        </Card>

        <Card
          title="Frameworks"
          description="Adapters that can render a UI document. Switching between available ones never changes the document."
        >
          <ul className="flex flex-col divide-y divide-app-border text-sm">
            {frameworks.data?.frameworks.map((framework) => {
              const own = implementedComponents(framework.id).length;
              return (
                <li key={framework.id} className="flex items-center gap-3 py-2">
                  <span className="w-32 shrink-0 font-medium">{framework.name}</span>
                  <span className="flex-1 text-app-muted">{framework.description}</span>
                  {usable.includes(framework.id) ? (
                    <Badge tone="success">{own} components</Badge>
                  ) : (
                    <Badge>{framework.status === "planned" ? "Planned" : "No adapter"}</Badge>
                  )}
                </li>
              );
            })}
          </ul>
        </Card>

        <Card
          title="Runtime check"
          description="Whether this frontend can render everything the connected backend may generate."
        >
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
            <dt className="text-app-muted">Backend</dt>
            <dd className="font-mono text-xs">{API_BASE_URL}</dd>
            <dt className="text-app-muted">Schema version</dt>
            <dd>{capabilities.data?.schema_version ?? "—"}</dd>
            <dt className="text-app-muted">Components</dt>
            <dd>
              {frontend.components.length} supported here · {capabilities.data?.components.length ?? "—"}{" "}
              registered on the backend
            </dd>
            <dt className="text-app-muted">Operations</dt>
            <dd>{capabilities.data?.operations.join(", ") ?? "—"}</dd>
          </dl>
          {capabilities.isError && (
            <p role="alert" className="mt-3 flex items-center gap-2 text-sm text-app-danger">
              <AlertTriangle size={15} aria-hidden /> The backend could not be reached.
            </p>
          )}
          {gaps && !hasGaps(gaps) && (
            <p className="mt-3 flex items-center gap-2 text-sm text-app-success">
              <CheckCircle2 size={15} aria-hidden /> Frontend and backend agree on the UI vocabulary.
            </p>
          )}
          {gaps && hasGaps(gaps) && (
            <p role="alert" className="mt-3 flex items-start gap-2 text-sm text-app-warning">
              <AlertTriangle size={15} aria-hidden className="mt-0.5" />
              <span>
                This build cannot render: {[...gaps.components, ...gaps.chartTypes, ...gaps.frameworks].join(", ")}.
                Such components show a placeholder until the frontend is updated.
              </span>
            </p>
          )}
        </Card>

        <Card
          title="Data"
          description="Datasets the assistant can build interfaces from. Charts, tables and metrics bind to them by name."
        >
          <DataSourcesCard />
        </Card>
      </div>
    </div>
  );
}
