"""Create a non-secret Bifrost config for an OpenAI-compatible provider."""

from urllib.parse import urlsplit, urlunsplit


def gateway_config(provider_base_url: str) -> dict:
    parsed = urlsplit(provider_base_url.rstrip("/"))
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "MODEL_PROVIDER_BASE_URL must be an HTTPS URL without credentials or query"
        )
    path = parsed.path.rstrip("/")
    path = path.removesuffix("/v1")
    gateway_base = urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))
    return {
        "client": {
            "enable_logging": True,
            "disable_content_logging": True,
            "retain_content_in_object_storage": False,
        },
        "providers": {
            "custom": {
                "keys": [
                    {
                        "name": "provider-key",
                        "value": "env.MODEL_PROVIDER_API_KEY",
                        "models": ["*"],
                        "weight": 1,
                    }
                ],
                "network_config": {
                    "base_url": gateway_base,
                    "default_request_timeout_in_seconds": 90,
                    "max_retries": 0,
                },
                "custom_provider_config": {
                    "base_provider_type": "openai",
                    "allowed_requests": {"chat_completion": True},
                },
            }
        },
    }


def gateway_model(model: str) -> str:
    if not model.strip():
        raise ValueError("MODEL_PRIMARY is required")
    return model if model.startswith("custom/") else "custom/" + model
