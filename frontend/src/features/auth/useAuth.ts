import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import { authApi } from "@/services/api/auth";
import { queryKeys } from "@/services/api/queryKeys";
import { useAuthStore } from "@/stores/authStore";

/** Whether the connected backend requires signing in. */
export function useAuthConfig() {
  return useQuery({
    queryKey: queryKeys.authConfig,
    queryFn: ({ signal }) => authApi.config(signal),
    staleTime: Infinity,
  });
}

export function useSignIn(mode: "login" | "register") {
  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      mode === "login" ? authApi.login(credentials) : authApi.register(credentials),
    onSuccess: (session) => useAuthStore.getState().signIn(session.access_token, session.user),
  });
}

/** Ends the session and forgets everything fetched for it. */
export function useSignOut() {
  const queryClient = useQueryClient();
  return useCallback(() => {
    useAuthStore.getState().signOut();
    queryClient.clear();
  }, [queryClient]);
}
