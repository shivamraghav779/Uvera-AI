import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { isApiError } from "@/services/api/client";
import { usePreferencesStore } from "@/stores/preferencesStore";

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        // Client errors will not fix themselves; retry only transient failures.
        retry: (failures, error) =>
          failures < 2 && !(isApiError(error) && error.status !== null && error.status < 500),
        refetchOnWindowFocus: true,
      },
      mutations: { retry: false },
    },
  });
}

/** Applies the user's chrome preference to the document root. */
function ChromeTheme() {
  const theme = usePreferencesStore((state) => state.chromeTheme);
  useEffect(() => {
    document.documentElement.dataset.chrome = theme;
  }, [theme]);
  return null;
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return (
    <QueryClientProvider client={queryClient}>
      <ChromeTheme />
      {children}
    </QueryClientProvider>
  );
}
