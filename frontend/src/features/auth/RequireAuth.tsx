import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { CanvasSkeleton } from "@/components/feedback/Skeleton";
import { StateMessage } from "@/components/feedback/StateMessage";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores/authStore";

import { useAuthConfig } from "./useAuth";

/**
 * Sends visitors without a session to the sign-in page, when the backend
 * requires one. The server enforces access on every request regardless; this
 * only decides which screen to show.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const token = useAuthStore((state) => state.token);
  const config = useAuthConfig();
  const location = useLocation();

  if (config.isPending) return <CanvasSkeleton label="Connecting" />;
  if (config.isError) {
    return (
      <StateMessage
        tone="error"
        title="The server cannot be reached"
        description={config.error.message}
        action={
          <Button variant="primary" onClick={() => void config.refetch()}>
            Try again
          </Button>
        }
      />
    );
  }
  if (config.data.auth_required && !token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
