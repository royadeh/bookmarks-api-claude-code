from urllib.parse import urlsplit, urlunsplit

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048
INVALID_URL_MESSAGE = (
    "url must be an http or https URL without credentials, at most 2048 characters"
)


def normalize_url(raw: str) -> str:
    url = raw.strip()
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(INVALID_URL_MESSAGE)
    parts = urlsplit(url)
    if parts.scheme.lower() not in ALLOWED_SCHEMES or not parts.hostname:
        raise ValueError(INVALID_URL_MESSAGE)
    if "@" in parts.netloc:
        raise ValueError(INVALID_URL_MESSAGE)
    return urlunsplit(parts._replace(scheme=parts.scheme.lower(), netloc=parts.netloc.lower()))
