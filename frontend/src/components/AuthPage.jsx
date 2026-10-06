import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LoaderCircle,
  Send,
  ShieldCheck,
} from "lucide-react";
import preview from "../assets/dashboard-preview.jpg";

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.9h11c-.5 2.5-1.9 4.7-4 6.1v5.1h6.5c3.8-3.5 6.1-8.6 6.1-15z"
      />
      <path
        fill="#34A853"
        d="M24 44c5.4 0 9.9-1.8 13.3-4.9l-6.5-5.1c-1.8 1.2-4.1 1.9-6.8 1.9-5.2 0-9.5-3.5-11.1-8.2H6.2v5.2C9.5 39.5 16.2 44 24 44z"
      />
      <path
        fill="#FBBC05"
        d="M12.9 27.7c-.4-1.2-.6-2.4-.6-3.7s.2-2.5.6-3.7v-5.2H6.2A20 20 0 0 0 4 24c0 3.2.8 6.2 2.2 8.9z"
      />
      <path
        fill="#EA4335"
        d="M24 12.1c2.9 0 5.5 1 7.5 2.9l5.6-5.6C33.9 6 29.4 4 24 4 16.2 4 9.5 8.5 6.2 15.1l6.7 5.2c1.6-4.7 5.9-8.2 11.1-8.2z"
      />
    </svg>
  );
}
export default function AuthPage({
  mode,
  config,
  client,
  navigate,
  onSignedIn,
  recoveryAllowed,
  onRecoveryCompleted,
}) {
  const signup = mode === "signup",
    reset = mode === "reset",
    recovery = mode === "recovery";
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [showPassword, setShowPassword] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!client) {
      setError("Account sign-in is being set up. Please check back shortly.");
      return;
    }
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if ((signup || recovery) && values.password !== values.confirm) {
      setError("The passwords do not match.");
      return;
    }
    if (recovery && !recoveryAllowed) {
      setError("Open the password reset link from your email first.");
      return;
    }
    setBusy(true);
    try {
      let result;
      if (reset)
        result = await client.auth.resetPasswordForEmail(values.email, {
          redirectTo: window.location.origin + "/auth/recovery",
        });
      else if (recovery)
        result = await client.auth.updateUser({ password: values.password });
      else if (signup)
        result = await client.auth.signUp({
          email: values.email,
          password: values.password,
          options: {
            data: { full_name: values.name.trim() },
            emailRedirectTo: window.location.origin + "/auth/callback",
          },
        });
      else
        result = await client.auth.signInWithPassword({
          email: values.email,
          password: values.password,
        });
      if (result.error) throw result.error;
      if (reset)
        setMessage(
          "If an account exists, you’ll receive an email with a password reset link.",
        );
      else if (recovery) {
        onRecoveryCompleted?.();
        setMessage("Your password is updated. You can open your dashboard.");
      } else if (result.data.session) onSignedIn(result.data.session);
      else
        setMessage(
          "Check your email to confirm your account, then return to log in.",
        );
    } catch (err) {
      setError(
        err.message || "We couldn’t complete sign-in. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function google() {
    if (!client || !config.google_enabled) return;
    setError("");
    setBusy(true);
    const { error: authError } = await client.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin + "/auth/callback",
        scopes: "openid email profile",
      },
    });
    if (authError) {
      setError(authError.message);
      setBusy(false);
    }
  }
  const title = reset
    ? "Let’s get you back in."
    : recovery
      ? "A fresh password."
      : signup
        ? "Your next chapter starts here."
        : "Welcome back.";
  return (
    <div className="auth-page">
      <aside className="auth-story">
        <a
          className="brand"
          href="/"
          onClick={(event) => {
            event.preventDefault();
            navigate("/");
          }}
        >
          <span className="brand-mark">
            <Send size={21} />
          </span>
          ApplyPilot
        </a>
        <div className="auth-story-copy">
          <span className="eyebrow">A LITTLE LESS ON YOUR PLATE</span>
          <h2>
            Your ambition.
            <br />
            Your next move.
            <br />
            <span>Your copilot.</span>
          </h2>
          <p>
            A workspace for discovering opportunities and preparing
            applications, with you in control.
          </p>
        </div>
        <div className="auth-story-preview">
          <img
            src={preview}
            alt="Preview of the ApplyPilot job discovery and application dashboard"
          />
        </div>
        <p className="auth-story-note">
          <ShieldCheck size={16} /> Prepared by agents. Approved by you.
        </p>
      </aside>
      <main className="auth-main">
        <button className="text-button auth-back" onClick={() => navigate("/")}>
          <ArrowLeft size={15} /> Back to home
        </button>
        <div className="auth-form-card">
          <span className="eyebrow">
            {signup
              ? "CREATE YOUR ACCOUNT"
              : reset || recovery
                ? "ACCOUNT RECOVERY"
                : "YOUR WORKSPACE IS WAITING"}
          </span>
          <h1>{title}</h1>
          <p className="auth-description">
            {reset
              ? "Enter your account email and we’ll send a reset link."
              : recovery
                ? "Choose a new password for your account."
                : signup
                  ? "Save your profile and applications in one place."
                  : "Log in to pick up where you left off."}
          </p>
          {!reset && !recovery && (
            <>
              <button
                className="google-button"
                disabled={busy || !config.google_enabled}
                onClick={google}
              >
                <GoogleMark /> Continue with Google
              </button>
              {config.enabled && !config.google_enabled && (
                <p className="auth-provider-note">
                  Google sign-in is not available yet. You can use email
                  instead.
                </p>
              )}
              <div className="auth-divider">
                <span />
                or continue with email
                <span />
              </div>
            </>
          )}
          {!config.enabled && (
            <p className="auth-setup-note">
              Account sign-in is being set up. The public home page is available
              to explore.
            </p>
          )}
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          {message && (
            <p className="auth-success" role="status">
              {message}
            </p>
          )}
          <form onSubmit={submit}>
            {signup && (
              <label>
                Full name
                <input
                  name="name"
                  autoComplete="name"
                  required
                  maxLength={120}
                  placeholder="Your name"
                />
              </label>
            )}
            {!recovery && (
              <label>
                Email address
                <input
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="you@example.com"
                />
              </label>
            )}
            {!reset && (
              <>
                <label>
                  Password
                  <div className="password-field">
                    <input
                      name="password"
                      type={showPassword ? "text" : "password"}
                      minLength={signup || recovery ? 8 : undefined}
                      maxLength={128}
                      autoComplete={
                        signup || recovery ? "new-password" : "current-password"
                      }
                      required
                      placeholder={
                        signup || recovery
                          ? "At least 8 characters"
                          : "Enter your password"
                      }
                    />
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    </button>
                  </div>
                </label>
                {(signup || recovery) && (
                  <label>
                    Confirm password
                    <input
                      name="confirm"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      minLength={8}
                      maxLength={128}
                      required
                      placeholder="Re-enter your password"
                    />
                  </label>
                )}
              </>
            )}
            {!signup && !reset && !recovery && (
              <button
                type="button"
                className="forgot-password"
                onClick={() => navigate("/reset-password")}
              >
                Forgot your password?
              </button>
            )}
            <button
              className="primary auth-submit"
              disabled={busy || !config.enabled}
            >
              {busy ? <LoaderCircle className="spin" size={17} /> : null}
              {reset
                ? "Send reset link"
                : recovery
                  ? "Update password"
                  : signup
                    ? "Create account"
                    : "Log in"}
              <ArrowRight size={16} />
            </button>
          </form>
          <div className="auth-switch">
            {reset || recovery ? (
              <button
                onClick={() =>
                  navigate(recovery && message ? "/app" : "/login")
                }
              >
                {recovery && message ? "Open dashboard" : "Back to log in"}
              </button>
            ) : (
              <>
                {signup ? "Already have an account?" : "New to ApplyPilot?"}
                <button onClick={() => navigate(signup ? "/login" : "/signup")}>
                  {signup ? "Log in" : "Create an account"}
                </button>
              </>
            )}
          </div>
          <p className="auth-boundary">
            <ShieldCheck size={13} /> Applications are prepared and submitted in
            our sandbox.
          </p>
        </div>
      </main>
    </div>
  );
}
