/**
 * Data the generated UIs can use. Uploading a CSV here makes it available to
 * the assistant as a dataset; the server parses and validates it, and reads
 * every source once before saving it.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Upload } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Field, TextArea, TextInput } from "@/components/ui/Field";
import { isApiError } from "@/services/api/client";
import { dataSourcesApi } from "@/services/api/dataSources";
import { queryKeys } from "@/services/api/queryKeys";
import { toast } from "@/stores/toastStore";

const MAX_FILE_BYTES = 1_000_000;

/** A dataset name the backend accepts, derived from a file or source name. */
export function toDatasetName(text: string): string {
  const cleaned = text
    .toLowerCase()
    .replace(/\.[a-z0-9]+$/, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return (/^[a-z]/.test(cleaned) ? cleaned : `data_${cleaned}`).slice(0, 64);
}

export function DataSourcesCard() {
  const queryClient = useQueryClient();
  const sources = useQuery({ queryKey: queryKeys.dataSources, queryFn: ({ signal }) => dataSourcesApi.list(signal) });
  const datasets = useQuery({ queryKey: queryKeys.datasets, queryFn: ({ signal }) => dataSourcesApi.datasets(signal) });
  const [name, setName] = useState("");
  const [content, setContent] = useState("");

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.dataSources });
  };
  const create = useMutation({
    mutationFn: () =>
      dataSourcesApi.create({
        name: name.trim(),
        type: "file_upload",
        configuration: {
          dataset: toDatasetName(name),
          description: `${name.trim()} (uploaded).`,
          format: content.trimStart().startsWith("[") ? "json" : "csv",
          content,
        },
      }),
    onSuccess: (source) => {
      toast.success(`Dataset “${source.datasets[0]}” is ready to use.`);
      setName("");
      setContent("");
      refresh();
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => dataSourcesApi.remove(id),
    onSuccess: refresh,
    onError: () => toast.error("The data source could not be removed."),
  });

  const onFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_FILE_BYTES) {
      toast.error("That file is larger than 1 MB.");
      return;
    }
    setContent(await file.text());
    if (!name) setName(file.name.replace(/\.[^.]+$/, ""));
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    create.mutate();
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h3 className="mb-1.5 text-xs font-semibold tracking-wide text-app-muted uppercase">
          Available datasets
        </h3>
        {datasets.isError && <p className="text-sm text-app-danger">Datasets could not be loaded.</p>}
        <ul className="flex flex-col divide-y divide-app-border text-sm">
          {datasets.data?.map((dataset) => (
            <li key={dataset.name} className="py-1.5">
              <code className="font-mono text-xs font-medium">{dataset.name}</code>
              <span className="ml-2 text-app-muted">{dataset.description}</span>
              <div className="mt-0.5 text-xs text-app-muted">
                {dataset.fields.map((field) => `${field.name} (${field.kind})`).join(" · ")}
              </div>
            </li>
          ))}
          {datasets.data?.length === 0 && <li className="py-1.5 text-app-muted">No datasets yet.</li>}
        </ul>
      </div>

      {sources.data && sources.data.length > 0 && (
        <div>
          <h3 className="mb-1.5 text-xs font-semibold tracking-wide text-app-muted uppercase">
            Your data sources
          </h3>
          <ul className="flex flex-col gap-1 text-sm">
            {sources.data.map((source) => (
              <li key={source.id} className="flex items-center gap-2">
                <span className="font-medium">{source.name}</span>
                <Badge>{source.type.replace("_", " ")}</Badge>
                <span className="flex-1 truncate text-xs text-app-muted">{source.datasets.join(", ")}</span>
                <IconButton
                  label={`Remove ${source.name}`}
                  disabled={remove.isPending}
                  onClick={() => remove.mutate(source.id)}
                >
                  <Trash2 size={14} />
                </IconButton>
              </li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={submit} className="flex flex-col gap-3 rounded-lg border border-app-border p-3">
        <h3 className="text-sm font-semibold">Add a dataset from CSV or JSON</h3>
        <Field label="Name">
          {(id) => (
            <TextInput
              id={id}
              required
              maxLength={120}
              placeholder="Support tickets"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          )}
        </Field>
        {name.trim() && (
          <p className="-mt-2 text-xs text-app-muted">
            The assistant will know it as <code className="font-mono">{toDatasetName(name)}</code>.
          </p>
        )}
        <Field label="Rows (CSV with a header row, or a JSON list of records)">
          {(id) => (
            <TextArea
              id={id}
              required
              rows={5}
              spellCheck={false}
              placeholder={"id,status,hours\n1,open,2.5\n2,closed,4"}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              className="font-mono text-xs"
            />
          )}
        </Field>
        {create.isError && (
          <p role="alert" className="text-sm text-app-danger">
            {isApiError(create.error) ? create.error.message : "The dataset could not be added."}
          </p>
        )}
        <div className="flex items-center gap-2">
          <Button type="submit" variant="primary" size="sm" busy={create.isPending}>
            Add dataset
          </Button>
          <label className="inline-flex h-7 cursor-pointer items-center gap-1.5 rounded-md border border-app-border px-2.5 text-xs font-medium hover:bg-app-subtle">
            <Upload size={13} aria-hidden />
            Choose a file
            <input type="file" accept=".csv,.json,text/csv,application/json" onChange={onFile} className="sr-only" />
          </label>
        </div>
        <p className="text-xs text-app-muted">
          REST API and PostgreSQL sources are registered through the API (
          <code className="font-mono">POST /api/v1/data-sources</code>); their credentials stay on the
          server.
        </p>
      </form>
    </div>
  );
}
