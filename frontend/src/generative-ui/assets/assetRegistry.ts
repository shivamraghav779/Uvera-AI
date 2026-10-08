/**
 * Resolves asset references of a document to image URLs.
 *
 * A component names an image by asset id. The id must be listed in the
 * document's application assets, whose URL is validated to be a path of this
 * application's own asset endpoint. So whatever a document says, an image can
 * only ever load from the backend the app is connected to.
 */
import { API_BASE_URL } from "@/services/api/client";

import type { Asset, UIDocument } from "../schema/types";

const ASSET_PATH = /^\/api\/v1\/assets\/[0-9a-f-]{36}\/content$/;

export function buildAssetIndex(document: UIDocument): ReadonlyMap<string, Asset> {
  return new Map((document.application?.assets ?? []).map((asset) => [asset.id, asset]));
}

/** Absolute URL of a stored asset on the connected backend. */
export function assetSource(asset: Pick<Asset, "url">): string {
  // Validated by the schema already; checked again because this value becomes a URL.
  return ASSET_PATH.test(asset.url) ? `${API_BASE_URL}${asset.url}` : "";
}

/** Assets of a document that no component refers to (shown as unused in the editor). */
export function unusedAssetIds(document: UIDocument, referenced: ReadonlySet<string>): string[] {
  return (document.application?.assets ?? [])
    .map((asset) => asset.id)
    .filter((assetId) => !referenced.has(assetId));
}
