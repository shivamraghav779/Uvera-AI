import { apiRequest } from "./client";
import type { Api, DataSourceRead } from "./types";

export type DatasetDescriptor = Api["DatasetDescriptor"];
export type DataSourceCreate = Api["DataSourceCreate"];

export const dataSourcesApi = {
  list: (signal?: AbortSignal) => apiRequest<DataSourceRead[]>("/data-sources", { signal }),
  /** Every dataset a generated UI can bind to: the user's sources plus demo data. */
  datasets: (signal?: AbortSignal) =>
    apiRequest<DatasetDescriptor[]>("/data-sources/datasets", { signal }),
  /** The server reads the source once before saving it; unreachable sources are refused. */
  create: (body: DataSourceCreate) =>
    apiRequest<DataSourceRead>("/data-sources", { method: "POST", body, timeoutMs: 30_000 }),
  remove: (dataSourceId: string) =>
    apiRequest<void>(`/data-sources/${dataSourceId}`, { method: "DELETE" }),
};
