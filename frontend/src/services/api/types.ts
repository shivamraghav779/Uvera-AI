/** Names for the API types generated from the backend's OpenAPI document. */
import type { components } from "./schema";

export type Api = components["schemas"];

export type WorkspaceRead = Api["WorkspaceRead"];
export type MessageRead = Api["MessageRead"];
export type VersionSummary = Api["VersionSummary"];
export type VersionDetail = Api["VersionDetail"];
export type VersionComparison = Api["VersionComparison"];
export type VersionCreate = Api["VersionCreate"];
export type ChangeRead = Api["ChangeRead"];
export type ProposalRead = Api["ProposalRead"];
export type ProposalStep = Api["ProposalStep"];
export type GenerateUIRequest = Api["GenerateUIRequest"];
export type MutateUIRequest = Api["MutateUIRequest"];
export type ThemeCatalog = Api["ThemeCatalogResponse"];
export type FrameworkCatalog = Api["FrameworkCatalogResponse"];
export type Capabilities = Api["CapabilitiesResponse"];
export type ComponentCatalog = Api["ComponentCatalogResponse"];
export type ActionExecuteResponse = Api["ActionExecuteResponse"];
export type DataSourceRead = Api["DataSourceRead"];
export type VersionSource = VersionSummary["source"];
export type GenerationJobCreate = Api["GenerationJobCreate"];
export type GenerationJobRead = Api["GenerationJobRead"];
export type JobStage = GenerationJobRead["stage"];
export type ApplicationSummary = Api["ApplicationSummary"];
export type QualityRead = Api["QualityRead"];
