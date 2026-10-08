import type { VersionSource, VersionSummary } from "@/services/api/types";

const SOURCE_LABELS: Record<VersionSource, string> = {
  ai_generation: "AI generated",
  ai_mutation: "AI edit",
  manual_edit: "Manual edit",
  restore: "Restore",
};

export function sourceLabel(source: VersionSource): string {
  return SOURCE_LABELS[source];
}

/** The version an applied proposal produced, if any. */
export function versionForProposal(
  versions: readonly VersionSummary[],
  proposalId: string | undefined,
): VersionSummary | undefined {
  if (!proposalId) return undefined;
  return versions.find((version) => version.metadata?.proposal_id === proposalId);
}

export function currentVersion(versions: readonly VersionSummary[]): VersionSummary | undefined {
  return versions.find((version) => version.is_current);
}
