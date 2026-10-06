import { createClient } from "@supabase/supabase-js";
let client;
let tokenProvider = async () => null;
export function initializeAuth(config) {
  if (config.enabled && !client)
    client = createClient(config.url, config.publishable_key, {
      auth: {
        flowType: "pkce",
        detectSessionInUrl: true,
        persistSession: true,
        autoRefreshToken: true,
      },
    });
  tokenProvider = async () =>
    client ? (await client.auth.getSession()).data.session?.access_token : null;
  return client;
}
export const accessToken = () => tokenProvider();
