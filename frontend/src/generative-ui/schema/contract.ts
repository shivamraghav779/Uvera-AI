/**
 * Compile-time link between the frontend schema and the backend's OpenAPI types.
 *
 * `services/api/schema.d.ts` is generated from the backend. If the backend
 * renames a field, changes an enum or makes something required, one of these
 * assertions stops compiling, so the two vocabularies cannot drift apart
 * unnoticed. (New *optional* backend fields are caught by the contract-fixture
 * tests instead, because the runtime schemas are strict.)
 */
import type { components } from "@/services/api/schema";

import type { Operation } from "../mutation/mutationTypes";

import type { Theme, UIDocument } from "./types";

type Api = components["schemas"];

type Assert<T extends true> = T;
type AssignableTo<From, To> = [From] extends [To] ? true : false;

/** Everything the frontend treats as a document is a document to the backend. */
export type DocumentConformsToApi = Assert<AssignableTo<UIDocument, Api["UIDocument"]>>;
export type ThemeConformsToApi = Assert<AssignableTo<Theme, Api["Theme"]>>;

type ApiOperation = NonNullable<Api["VersionCreate"]["operations"]>[number];
/** The two sides agree on the set of operation types. */
export type OperationTypesMatch = Assert<
  AssignableTo<Operation["type"], ApiOperation["type"]> &
    AssignableTo<ApiOperation["type"], Operation["type"]>
>;

type ApiComponentType = Api["ComponentRead"]["type"];
type FrontendComponentType = UIDocument["page"]["type"] | UIDocument["page"]["components"][number]["type"];
/** The two sides agree on the set of component types. */
export type ComponentTypesMatch = Assert<
  AssignableTo<FrontendComponentType, ApiComponentType> &
    AssignableTo<ApiComponentType, FrontendComponentType>
>;
