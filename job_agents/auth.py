"""Verify managed account sessions at the authentication provider, never trust decoded JWTs."""

import base64
import json
import os
from uuid import UUID

import httpx
from fastapi import HTTPException


class Accounts:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
        self.enabled = bool(self.url and self.key)
        self.required = bool(self.url or self.key) or os.environ.get("AUTH_REQUIRED") == "1"
        if self.enabled and not self.url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        legacy_role = ""
        if self.key.count(".") == 2:
            try:
                encoded = self.key.split(".")[1]
                legacy_role = json.loads(
                    base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
                ).get("role", "")
            except (ValueError, TypeError, AttributeError):
                pass
        if self.key.startswith("sb_secret_") or legacy_role == "service_role":
            raise ValueError("Use a public Supabase publishable/anon key, not a secret key")

    async def verify(self, authorization: str) -> dict:
        if not self.enabled:
            raise HTTPException(503, "Account sign-in is not configured yet.")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or len(token) > 16000:
            raise HTTPException(401, "Sign in to continue.")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.url + "/auth/v1/user",
                    headers={"apikey": self.key, "Authorization": "Bearer " + token},
                )
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Sign-in service is unavailable. Try again shortly.") from exc
        if response.status_code in (401, 403):
            raise HTTPException(401, "Your session has expired. Please sign in again.")
        if response.status_code != 200:
            raise HTTPException(503, "Sign-in service is unavailable. Try again shortly.")
        try:
            user = response.json()
            UUID(user["id"])
            if not user.get("email_confirmed_at"):
                raise ValueError("Unverified email")
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(401, "Confirm your email before continuing.") from exc
        name = user.get("user_metadata", {}).get("full_name", "")
        return {
            "id": user["id"],
            "email": user.get("email", ""),
            "name": name if isinstance(name, str) else "",
        }

    async def public_config(self):
        google = False
        if self.enabled:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        self.url + "/auth/v1/settings", headers={"apikey": self.key}
                    )
                if response.status_code == 200:
                    google = bool(response.json().get("external", {}).get("google"))
            except (httpx.HTTPError, ValueError):
                pass
        return {
            "enabled": self.enabled,
            "demo_mode": not self.required,
            "url": self.url if self.enabled else "",
            "publishable_key": self.key if self.enabled else "",
            "google_enabled": google,
        }
