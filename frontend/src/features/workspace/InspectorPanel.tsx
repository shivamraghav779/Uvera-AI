/**
 * Properties of the selected component. Every control here produces an
 * operation (UPDATE, RESIZE, STYLE, MOVE, DELETE); the inspector never writes
 * to the document directly.
 */
import { ArrowDown, ArrowUp, ChevronRight, Sparkles, Trash2, X } from "lucide-react";

import { Button, IconButton } from "@/components/ui/Button";
import { Field, SelectInput, TextArea, TextInput } from "@/components/ui/Field";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { getComponentDefinition, type EditableField } from "@/generative-ui/registry/componentRegistry";
import { findLocation } from "@/generative-ui/schema/tree";
import type { PageNode, UIComponent } from "@/generative-ui/schema/types";
import {
  COLOR_ROLES,
  EMPHASIS_LEVELS,
  GRID_COLUMNS,
  HEIGHT_PRESETS,
  SURFACE_VARIANTS,
} from "@/generative-ui/schema/validators";
import { useSyncedDraft } from "@/hooks/useSyncedDraft";

import {
  nudgeOperation,
  selectionAfterDelete,
  selectionPath,
  typeLabel,
} from "@/generative-ui/workspace/SelectionManager";

interface InspectorPanelProps {
  page: PageNode;
  selectedId: string | null;
  onApply: (operations: Operation[]) => void;
  onSelect: (componentId: string | null) => void;
  onAsk: () => void;
  onClose: () => void;
}

const SPAN_PRESETS = [3, 4, 6, 8, 12];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-2.5 border-b border-app-border p-3">
      <h3 className="text-xs font-semibold tracking-wide text-app-muted uppercase">{title}</h3>
      {children}
    </section>
  );
}

/** A text control that commits on blur or Enter, so typing does not spam operations. */
function CommitInput({
  id,
  value,
  multiline,
  numeric,
  onCommit,
}: {
  id: string;
  value: string;
  multiline?: boolean;
  numeric?: boolean;
  onCommit: (value: string) => void;
}) {
  const [draft, setDraft] = useSyncedDraft(value);
  const commit = () => {
    if (draft !== value) onCommit(draft);
  };
  if (multiline) {
    return (
      <TextArea id={id} rows={3} value={draft} onChange={(e) => setDraft(e.target.value)} onBlur={commit} />
    );
  }
  return (
    <TextInput
      id={id}
      type={numeric ? "number" : "text"}
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
    />
  );
}

function PropertyField({
  field,
  node,
  onUpdate,
}: {
  field: EditableField;
  node: UIComponent;
  onUpdate: (key: string, value: unknown) => void;
}) {
  const current = (node as unknown as Record<string, unknown>)[field.key];
  if (field.kind === "boolean") {
    return (
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={current === true}
          onChange={(event) => onUpdate(field.key, event.target.checked)}
          className="size-3.5 accent-[var(--app-accent)]"
        />
        {field.label}
      </label>
    );
  }
  return (
    <Field label={field.label}>
      {(id) =>
        field.kind === "select" ? (
          <SelectInput id={id} value={String(current ?? "")} onChange={(e) => onUpdate(field.key, e.target.value)}>
            {field.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </SelectInput>
        ) : (
          <CommitInput
            id={id}
            value={current === undefined ? "" : String(current)}
            multiline={field.kind === "textarea"}
            numeric={field.kind === "number"}
            onCommit={(value) => {
              // An emptied optional field is removed (null), not stored as "".
              if (value.trim() === "") onUpdate(field.key, null);
              else onUpdate(field.key, field.kind === "number" ? Number(value) : value);
            }}
          />
        )
      }
    </Field>
  );
}

export function InspectorPanel({ page, selectedId, onApply, onSelect, onAsk, onClose }: InspectorPanelProps) {
  const location = selectedId ? findLocation(page, selectedId) : null;

  const header = (
    <header className="flex h-10 shrink-0 items-center justify-between border-b border-app-border px-3">
      <h2 className="text-sm font-semibold">Inspector</h2>
      <IconButton label="Close inspector" onClick={onClose} className="size-7">
        <X size={15} />
      </IconButton>
    </header>
  );

  if (!location || !selectedId) {
    return (
      <aside aria-label="Inspector" className="flex h-full flex-col">
        {header}
        <p className="p-4 text-sm text-app-muted">
          Select a component on the canvas to change its size, style and content. You can also select
          one and tell the assistant what to do with “this”.
        </p>
      </aside>
    );
  }

  const node = location.node;
  const definition = getComponentDefinition(node.type);
  const path = selectionPath(page, selectedId);
  const update = (key: string, value: unknown) =>
    onApply([{ type: "UPDATE", target: node.id, props: { [key]: value } }]);
  const nudge = (direction: -1 | 1) => {
    const operation = nudgeOperation(page, node.id, direction);
    if (operation) onApply([operation]);
  };
  const remove = () => {
    onSelect(selectionAfterDelete(page, node.id));
    onApply([{ type: "DELETE", target: node.id }]);
  };

  return (
    <aside aria-label="Inspector" className="flex h-full flex-col">
      {header}
      <div className="flex-1 overflow-y-auto">
        <Section title={typeLabel(node.type)}>
          <nav aria-label="Selection path" className="flex flex-wrap items-center gap-0.5 text-xs text-app-muted">
            <button type="button" onClick={() => onSelect(null)} className="rounded px-1 hover:bg-app-subtle">
              Page
            </button>
            {path.map((crumb) => (
              <span key={crumb.id} className="flex items-center gap-0.5">
                <ChevronRight size={11} aria-hidden />
                <button
                  type="button"
                  onClick={() => onSelect(crumb.id)}
                  aria-current={crumb.id === node.id ? "true" : undefined}
                  className="rounded px-1 hover:bg-app-subtle aria-[current]:font-medium aria-[current]:text-app-fg"
                >
                  {crumb.label}
                </button>
              </span>
            ))}
          </nav>
          <p className="text-xs text-app-muted">
            Id <code className="rounded bg-app-subtle px-1 py-0.5 font-mono text-app-fg">{node.id}</code>
          </p>
          <Button size="sm" icon={<Sparkles size={13} />} onClick={onAsk}>
            Ask the assistant about this
          </Button>
        </Section>

        <Section title="Layout">
          <Field label={`Width — ${node.layout.span} of ${GRID_COLUMNS} columns`}>
            {(id) => (
              <input
                id={id}
                type="range"
                min={1}
                max={GRID_COLUMNS}
                value={node.layout.span}
                onChange={(event) =>
                  onApply([{ type: "RESIZE", target: node.id, span: Number(event.target.value) }])
                }
                className="accent-[var(--app-accent)]"
              />
            )}
          </Field>
          <div className="flex gap-1">
            {SPAN_PRESETS.map((span) => (
              <button
                key={span}
                type="button"
                aria-pressed={node.layout.span === span}
                onClick={() => onApply([{ type: "RESIZE", target: node.id, span }])}
                className="h-6 flex-1 rounded border border-app-border text-xs hover:bg-app-subtle aria-pressed:border-app-accent aria-pressed:bg-app-accent-soft"
              >
                {span === GRID_COLUMNS ? "Full" : `${span}/12`}
              </button>
            ))}
          </div>
          <Field label="Height">
            {(id) => (
              <SelectInput
                id={id}
                value={node.layout.height}
                onChange={(event) =>
                  onApply([
                    {
                      type: "RESIZE",
                      target: node.id,
                      height: event.target.value as (typeof HEIGHT_PRESETS)[number],
                    },
                  ])
                }
              >
                {HEIGHT_PRESETS.map((height) => (
                  <option key={height} value={height}>
                    {height}
                  </option>
                ))}
              </SelectInput>
            )}
          </Field>
          <div className="flex gap-1.5">
            <Button
              size="sm"
              icon={<ArrowUp size={13} />}
              onClick={() => nudge(-1)}
              disabled={location.index === 0}
              className="flex-1"
            >
              Earlier
            </Button>
            <Button
              size="sm"
              icon={<ArrowDown size={13} />}
              onClick={() => nudge(1)}
              disabled={location.index === location.siblings.length - 1}
              className="flex-1"
            >
              Later
            </Button>
          </div>
        </Section>

        <Section title="Style">
          <Field label="Tone">
            {(id) => (
              <SelectInput
                id={id}
                value={node.style?.tone ?? ""}
                onChange={(event) =>
                  onApply([
                    {
                      type: "STYLE",
                      target: node.id,
                      style: { tone: (event.target.value || null) as (typeof COLOR_ROLES)[number] | null },
                    },
                  ])
                }
              >
                <option value="">Default</option>
                {COLOR_ROLES.map((tone) => (
                  <option key={tone} value={tone}>
                    {tone}
                  </option>
                ))}
              </SelectInput>
            )}
          </Field>
          <Field label="Emphasis">
            {(id) => (
              <SelectInput
                id={id}
                value={node.style?.emphasis ?? ""}
                onChange={(event) =>
                  onApply([
                    {
                      type: "STYLE",
                      target: node.id,
                      style: {
                        emphasis: (event.target.value || null) as (typeof EMPHASIS_LEVELS)[number] | null,
                      },
                    },
                  ])
                }
              >
                <option value="">Default</option>
                {EMPHASIS_LEVELS.map((emphasis) => (
                  <option key={emphasis} value={emphasis}>
                    {emphasis}
                  </option>
                ))}
              </SelectInput>
            )}
          </Field>
          <Field label="Surface">
            {(id) => (
              <SelectInput
                id={id}
                value={node.style?.surface ?? ""}
                onChange={(event) =>
                  onApply([
                    {
                      type: "STYLE",
                      target: node.id,
                      style: { surface: (event.target.value || null) as (typeof SURFACE_VARIANTS)[number] | null },
                    },
                  ])
                }
              >
                <option value="">From the visual style</option>
                {SURFACE_VARIANTS.map((surface) => (
                  <option key={surface} value={surface}>
                    {surface}
                  </option>
                ))}
              </SelectInput>
            )}
          </Field>
        </Section>

        {definition && definition.fields.length > 0 && (
          <Section title="Content">
            {definition.fields.map((field) => (
              <PropertyField key={`${node.id}:${field.key}`} field={field} node={node} onUpdate={update} />
            ))}
          </Section>
        )}

        <div className="p-3">
          <Button size="sm" variant="ghost" icon={<Trash2 size={13} />} onClick={remove} className="text-app-danger">
            Delete component
          </Button>
        </div>
      </div>
    </aside>
  );
}
