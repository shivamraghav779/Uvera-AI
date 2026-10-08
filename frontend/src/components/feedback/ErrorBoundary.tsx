import { Component, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";

import { StateMessage } from "./StateMessage";

/** Last line of defence for the application shell. */
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  override state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  override render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="h-full">
        <StateMessage
          tone="error"
          title="Something went wrong"
          description="The application hit an unexpected error. Your saved workspaces are not affected."
          action={
            <Button variant="primary" onClick={() => window.location.reload()}>
              Reload
            </Button>
          }
        />
      </div>
    );
  }
}
