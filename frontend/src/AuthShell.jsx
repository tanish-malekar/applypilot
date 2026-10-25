import { useEffect, useState } from "react";
import { LoaderCircle } from "lucide-react";
import App from "./App.jsx";
import Landing from "./components/Landing.jsx";
import PrivacyPage from "./components/PrivacyPage.jsx";
import AuthPage from "./components/AuthPage.jsx";
import { initializeAuth } from "./auth.js";

export default function AuthShell() {
  const [path, setPath] = useState(window.location.pathname);
  const [config, setConfig] = useState(null),
    [client, setClient] = useState(null),
    [session, setSession] = useState(null);
  const [ready, setReady] = useState(false),
    [error, setError] = useState("");
  const [recoveryAllowed, setRecoveryAllowed] = useState(
    () =>
      Number(sessionStorage.getItem("applypilot:recovery")) >
      Date.now() - 900000,
  );
  function navigate(next, replace = false) {
    if (!next.startsWith("/") || next.startsWith("//")) next = "/";
    window.history[replace ? "replaceState" : "pushState"]({}, "", next);
    setPath(next);
    window.scrollTo(0, 0);
  }
  useEffect(() => {
    let active = true,
      subscription;
    const pop = () => setPath(window.location.pathname);
    window.addEventListener("popstate", pop);
    async function boot() {
      try {
        const callbackError = new URLSearchParams(window.location.search).get(
          "error_description",
        );
        if (callbackError && window.location.pathname.startsWith("/auth/"))
          setError(callbackError.slice(0, 500));
        const response = await fetch("/api/auth/config", {
          signal: AbortSignal.timeout(60000),
        });
        if (!response.ok)
          throw new Error(
            "Couldn’t load account settings. Please reload to try again.",
          );
        const settings = await response.json();
        if (!active) return;
        setConfig(settings);
        const authClient = initializeAuth(settings);
        setClient(authClient);
        if (authClient) {
          subscription = authClient.auth.onAuthStateChange((event, updated) => {
            if (!active) return;
            setSession(updated);
            if (event === "PASSWORD_RECOVERY") {
              sessionStorage.setItem("applypilot:recovery", String(Date.now()));
              setRecoveryAllowed(true);
              navigate("/auth/recovery", true);
            }
          }).data.subscription;
          const { data, error: sessionError } =
            await authClient.auth.getSession();
          if (sessionError) throw sessionError;
          if (active) setSession(data.session);
        }
      } catch (err) {
        if (active)
          setError(
            err.name === "TimeoutError" || err.name === "AbortError"
              ? "Account services are taking longer than expected. Please try again shortly."
              : err.message,
          );
      } finally {
        if (active) setReady(true);
      }
    }
    boot();
    return () => {
      active = false;
      subscription?.unsubscribe();
      window.removeEventListener("popstate", pop);
    };
  }, []);
  useEffect(() => {
    if (!ready) return;
    if (session && ["/login", "/signup", "/auth/callback"].includes(path))
      navigate("/app", true);
    else if (!session && path === "/app") navigate("/login", true);
    else if (path === "/demo" && config && !config.demo_mode)
      navigate(session ? "/app" : "/login", true);
    else if (path === "/auth/callback" && !session) navigate("/login", true);
  }, [path, session, ready, config]);
  useEffect(() => {
    const expired = () => {
      setSession(null);
      navigate("/login", true);
    };
    window.addEventListener("applypilot:unauthorized", expired);
    return () => window.removeEventListener("applypilot:unauthorized", expired);
  }, []);
  async function signOut() {
    if (client) {
      const { error: signoutError } = await client.auth.signOut({
        scope: "local",
      });
      if (signoutError) {
        setError(signoutError.message);
        return;
      }
    }
    setSession(null);
    navigate("/");
  }
  // Public pages must remain readable while account services wake or recover.
  // Account routes still wait for configuration and never fall back to a demo.
  if (path === "/")
    return (
      <Landing
        navigate={navigate}
        user={session?.user}
        demoMode={Boolean(config?.demo_mode)}
        accountsReady={config ? config.enabled : true}
      />
    );
  if (path === "/privacy") return <PrivacyPage navigate={navigate} />;
  if (!ready)
    return (
      <div className="site-loading" role="status">
        <LoaderCircle className="spin" size={26} />
        <p>Opening ApplyPilot…</p>
      </div>
    );
  if (error && !config)
    return (
      <div className="site-loading">
        <p role="alert">{error}</p>
        <button className="primary" onClick={() => window.location.reload()}>
          Try again
        </button>
      </div>
    );
  const authPaths = {
    "/login": "login",
    "/signup": "signup",
    "/reset-password": "reset",
    "/auth/recovery": "recovery",
  };
  const settings = config || {
    enabled: false,
    demo_mode: false,
    google_enabled: false,
  };
  return (
    <>
      {error && (
        <div className="global-auth-error" role="alert">
          {error}
          <button onClick={() => setError("")}>Dismiss</button>
        </div>
      )}
      {path === "/privacy" ? (
        <PrivacyPage navigate={navigate} />
      ) : authPaths[path] ? (
        <AuthPage
          key={path}
          mode={authPaths[path]}
          config={settings}
          client={client}
          navigate={navigate}
          recoveryAllowed={recoveryAllowed}
          onRecoveryCompleted={() => {
            sessionStorage.removeItem("applypilot:recovery");
            setRecoveryAllowed(false);
          }}
          onSignedIn={(updated) => {
            setSession(updated);
            navigate("/app", true);
          }}
        />
      ) : path === "/app" && session ? (
        <App
          key={session.user.id}
          user={session.user}
          onSignOut={signOut}
          onHome={() => navigate("/")}
        />
      ) : path === "/demo" && settings.demo_mode ? (
        <App key="demo" onHome={() => navigate("/")} />
      ) : (
        <Landing
          navigate={navigate}
          user={session?.user}
          demoMode={settings.demo_mode}
          accountsReady={settings.enabled}
        />
      )}
    </>
  );
}
