"""Security helpers (Road_Map Step 18)."""


def redact_secret(value: str | None) -> str:
    """Mask a secret, keeping a short prefix for identification.

    Used anywhere a credential or token might otherwise leak into logs or a
    response body.
    """
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return value[:4] + "****"
