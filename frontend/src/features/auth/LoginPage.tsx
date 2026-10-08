import { CircleAlert, Eye, EyeOff, GitBranch, MousePointerClick, ShieldCheck } from "lucide-react";
import { useId, useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router";

import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/Field";
import workspacePreview from "@/assets/workspace-preview.png";
import { cn } from "@/utils/cn";
import { isApiError } from "@/services/api/client";
import { useAuthStore } from "@/stores/authStore";

import { useAuthConfig, useSignIn } from "./useAuth";

type Mode = "login" | "register";

const COPY: Record<Mode, { title: string; submit: string; switchPrompt: string; switchAction: string }> = {
  login: {
    title: "Sign in",
    submit: "Sign in",
    switchPrompt: "New here?",
    switchAction: "Create an account",
  },
  register: {
    title: "Create your account",
    submit: "Create account",
    switchPrompt: "Already have an account?",
    switchAction: "Sign in",
  },
};

/** What the product does, stated on the showcase side. Only things that are true today. */
const HIGHLIGHTS = [
  { icon: MousePointerClick, text: "Preview every change before it is saved" },
  { icon: GitBranch, text: "Every version kept and restorable" },
  { icon: ShieldCheck, text: "Structured UI, never generated code" },
];

function failureMessage(error: unknown): string {
  if (isApiError(error, "NETWORK_ERROR")) return error.message;
  if (isApiError(error, "RATE_LIMIT_EXCEEDED")) return "Too many attempts. Wait a minute and try again.";
  if (isApiError(error, "VALIDATION_ERROR")) return "Enter a valid email address and password.";
  return isApiError(error) ? error.message : "Something went wrong. Please try again.";
}

export function LoginPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [revealed, setRevealed] = useState(false);
  const emailId = useId();
  const passwordId = useId();
  const token = useAuthStore((state) => state.token);
  const config = useAuthConfig();
  const signIn = useSignIn(mode);
  const location = useLocation();
  const copy = COPY[mode];
  const minLength = config.data?.min_password_length ?? 8;

  if (token || config.data?.auth_required === false) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? "/workspaces"} replace />;
  }

  const submit = (event: FormEvent) => {
    event.preventDefault();
    signIn.mutate({ email, password });
  };

  const switchTo = (next: Mode) => {
    if (next === mode) return;
    signIn.reset();
    setMode(next);
  };

  return (
    <main className="flex min-h-full flex-col bg-app-panel lg:flex-row">
      <section className="flex min-h-full w-full flex-col justify-between border-app-border p-8 sm:p-12 lg:w-[46%] lg:border-r lg:p-14">
        <div className="flex items-center gap-2.5">
          <span aria-hidden className="grid size-7 grid-cols-2 gap-0.5 rounded-md bg-app-fg p-1">
            <span className="rounded-[2px] bg-app-panel" />
            <span className="rounded-[2px] bg-app-muted" />
            <span className="col-span-2 rounded-[2px] bg-app-accent" />
          </span>
          <span className="text-sm font-semibold tracking-tight">Generative UI</span>
        </div>

        <div className="mx-auto my-auto w-full max-w-[390px] py-10">
          <div
            role="tablist"
            aria-label="Sign in or create an account"
            className="mb-8 flex w-full rounded-lg border border-app-border bg-app-subtle p-1"
          >
            {(["login", "register"] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={mode === value}
                onClick={() => switchTo(value)}
                className={cn(
                  "flex-1 rounded-md py-1.5 text-xs font-medium transition-colors",
                  mode === value ? "bg-app-panel text-app-fg shadow-sm" : "text-app-muted hover:text-app-fg",
                )}
              >
                {value === "login" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          <h1 className="text-2xl font-semibold tracking-tight">{copy.title}</h1>
          <p className="mt-1.5 mb-6 text-xs leading-relaxed text-app-muted">
            Your workspaces and their version history are private to your account.
          </p>

          <form onSubmit={submit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor={emailId} className="text-xs font-medium text-app-fg">
                Email
              </label>
              <TextInput
                id={emailId}
                type="email"
                autoComplete="email"
                placeholder="name@organization.com"
                required
                className="h-9 rounded-lg px-3"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={passwordId} className="text-xs font-medium text-app-fg">
                {mode === "register" ? `Password (at least ${minLength} characters)` : "Password"}
              </label>
              <div className="relative flex items-center">
                <TextInput
                  id={passwordId}
                  type={revealed ? "text" : "password"}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  required
                  minLength={mode === "register" ? minLength : undefined}
                  className="h-9 rounded-lg px-3 pr-9"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <button
                  type="button"
                  aria-label={revealed ? "Hide password" : "Show password"}
                  aria-pressed={revealed}
                  onClick={() => setRevealed((value) => !value)}
                  className="absolute right-2 rounded p-1 text-app-muted hover:text-app-fg"
                >
                  {revealed ? <EyeOff size={15} aria-hidden /> : <Eye size={15} aria-hidden />}
                </button>
              </div>
            </div>
            {signIn.isError && (
              <p
                role="alert"
                className="flex items-center gap-2 rounded-lg border border-[color-mix(in_srgb,var(--app-danger)_30%,transparent)] bg-[color-mix(in_srgb,var(--app-danger)_8%,transparent)] p-2.5 text-xs font-medium text-app-danger"
              >
                <CircleAlert size={15} aria-hidden className="shrink-0" />
                {failureMessage(signIn.error)}
              </p>
            )}
            <Button type="submit" variant="accent" busy={signIn.isPending} className="mt-2 h-9 w-full rounded-lg">
              {copy.submit}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-app-muted">
            {copy.switchPrompt}{" "}
            <button
              type="button"
              className="font-medium text-app-accent hover:underline"
              onClick={() => switchTo(mode === "login" ? "register" : "login")}
            >
              {copy.switchAction}
            </button>
          </p>
        </div>

        <p className="border-t border-app-border pt-6 text-[11px] text-app-muted">
          Generative UI · a conversational workspace for building interfaces
        </p>
      </section>

      <section
        aria-label="About Generative UI"
        className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-app-bg p-12 lg:flex xl:p-16"
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 [background-image:radial-gradient(var(--app-border)_1px,transparent_1px)] [background-size:20px_20px] opacity-60"
        />
        <div className="relative">
          <span className="inline-flex items-center gap-2 rounded-full border border-app-border bg-app-panel px-3 py-1 text-xs font-medium">
            <span aria-hidden className="size-2 rounded-full bg-app-accent" />
            AI interface workspace
          </span>
        </div>

        <div className="relative my-auto flex flex-col items-center py-8">
          <div className="w-full max-w-[620px] rounded-2xl border border-app-border bg-app-panel/70 p-2 shadow-app-modal">
            <img
              src={workspacePreview}
              alt="A workspace showing a generated sales dashboard with the assistant bar beneath it"
              className="block h-auto w-full rounded-xl border border-app-border"
            />
          </div>
          <h2 className="mt-8 max-w-[500px] text-center text-xl leading-snug font-semibold tracking-tight xl:text-2xl">
            Describe what you want to build, then shape it directly.
          </h2>
          <p className="mt-2 max-w-[500px] text-center text-xs leading-relaxed text-app-muted xl:text-sm">
            The assistant drafts dashboards and forms from your data. You approve each change, edit by hand
            when you prefer, and can go back to any version.
          </p>
        </div>

        <ul className="relative flex flex-wrap items-center justify-between gap-x-6 gap-y-2 rounded-xl border border-app-border bg-app-panel p-4">
          {HIGHLIGHTS.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-center gap-2 text-xs font-medium">
              <Icon size={14} aria-hidden className="text-app-accent" />
              {text}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
