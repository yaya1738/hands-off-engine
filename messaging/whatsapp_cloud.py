"""Guarded WhatsApp Business Cloud API sender.

No secrets are stored in source. Both recipient allowlisting and explicit
opt-in are required before any network request. Free-form text is only
accepted for an active 24-hour customer-service window; use an approved
template for business-initiated messages.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


_E164 = re.compile(r"^\+[1-9][0-9]{7,14}$")
_GRAPH_VERSION = re.compile(r"^v[0-9]+\.[0-9]+$")


class WhatsAppConfigurationError(RuntimeError):
    """Required WhatsApp configuration is absent or invalid."""


class WhatsAppRecipientDenied(PermissionError):
    """Recipient is not both allowlisted and opted in."""


class WhatsAppDeliveryError(RuntimeError):
    """WhatsApp Cloud API rejected or failed the send."""


def _csv_set(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, "").split(",") if item.strip()}


def _config() -> tuple[str, str, str]:
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    version = os.getenv("WHATSAPP_GRAPH_API_VERSION", "").strip()
    if not token or not phone_number_id or not version:
        raise WhatsAppConfigurationError(
            "Set WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, and "
            "WHATSAPP_GRAPH_API_VERSION in the runtime secret store."
        )
    if not _GRAPH_VERSION.fullmatch(version):
        raise WhatsAppConfigurationError("WHATSAPP_GRAPH_API_VERSION must look like v24.0.")
    return token, phone_number_id, version


def _authorize_recipient(recipient: str) -> str:
    normalized = recipient.strip()
    if not _E164.fullmatch(normalized):
        raise ValueError("Recipient must be an E.164 number such as +972547385735.")
    if normalized not in _csv_set("WHATSAPP_ALLOWED_RECIPIENTS"):
        raise WhatsAppRecipientDenied("Recipient is not in WHATSAPP_ALLOWED_RECIPIENTS.")
    if normalized not in _csv_set("WHATSAPP_OPTED_IN_RECIPIENTS"):
        raise WhatsAppRecipientDenied("Recipient has no recorded WhatsApp opt-in.")
    return normalized


def _post(payload: dict[str, Any], recipient: str, timeout: float = 15.0) -> dict[str, Any]:
    token, phone_number_id, version = _config()
    recipient = _authorize_recipient(recipient)
    url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
    body = dict(payload)
    body.update({"messaging_product": "whatsapp", "recipient_type": "individual", "to": recipient})
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not log or re-emit request headers, which contain the access token.
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise WhatsAppDeliveryError(f"WhatsApp API returned HTTP {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WhatsAppDeliveryError(f"WhatsApp API transport failed: {type(exc).__name__}") from None
    if not isinstance(result, dict) or not result.get("messages"):
        raise WhatsAppDeliveryError("WhatsApp API response did not confirm message acceptance.")
    return result


def send_text(recipient: str, text: str) -> dict[str, Any]:
    """Send free-form text inside the recipient's active 24-hour service window."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Message text cannot be empty.")
    if len(text) > 4096:
        raise ValueError("WhatsApp text messages are limited to 4096 characters.")
    return _post({"type": "text", "text": {"preview_url": False, "body": text}}, recipient)


def send_template(
    recipient: str,
    template_name: str,
    language_code: str = "en_US",
    components: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Send a pre-approved WhatsApp template for business-initiated messages."""
    if not re.fullmatch(r"[a-z0-9_]{1,128}", template_name):
        raise ValueError("Template name must be a valid lowercase WhatsApp template name.")
    if not re.fullmatch(r"[a-z]{2,3}_[A-Z]{2}", language_code):
        raise ValueError("Language code must look like en_US.")
    template: dict[str, Any] = {"name": template_name, "language": {"code": language_code}}
    if components:
        template["components"] = components
    return _post({"type": "template", "template": template}, recipient)
