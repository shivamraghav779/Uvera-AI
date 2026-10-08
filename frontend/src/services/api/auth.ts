import { apiRequest } from "./client";
import type { Api } from "./types";

export type TokenResponse = Api["TokenResponse"];
export type AuthConfig = Api["AuthConfig"];

interface Credentials {
  email: string;
  password: string;
}

export const authApi = {
  config: (signal?: AbortSignal) => apiRequest<AuthConfig>("/auth/config", { signal }),
  register: (body: Credentials) => apiRequest<TokenResponse>("/auth/register", { method: "POST", body }),
  login: (body: Credentials) => apiRequest<TokenResponse>("/auth/login", { method: "POST", body }),
};
