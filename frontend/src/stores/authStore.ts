/**
 * The signed-in session. The access token is the one piece of server-issued
 * state kept in the browser (localStorage), so a reload stays signed in. It is
 * a credential, not workspace content: workspaces always come from the API.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface SessionUser {
  id: string;
  email: string;
}

interface AuthState {
  token: string | null;
  user: SessionUser | null;
  signIn: (token: string, user: SessionUser) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      signIn: (token, user) => set({ token, user }),
      signOut: () => set({ token: null, user: null }),
    }),
    { name: "generative-ui.session", version: 1 },
  ),
);

/** Read outside React (the HTTP client). */
export const currentToken = (): string | null => useAuthStore.getState().token;
