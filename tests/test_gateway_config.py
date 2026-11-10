import pytest
from discoverybrief.gateway_config import gateway_config, gateway_model


def test_generic_gateway_configuration_does_not_embed_secrets():
    config = gateway_config("https://api.tokenrouter.com/v1")
    provider = config["providers"]["custom"]
    assert provider["network_config"]["base_url"] == "https://api.tokenrouter.com"
    assert provider["keys"][0]["value"] == "env.MODEL_PROVIDER_API_KEY"
    assert gateway_model("anthropic/example-model") == "custom/anthropic/example-model"
    assert (
        gateway_model("custom/anthropic/example-model")
        == "custom/anthropic/example-model"
    )


def test_provider_url_rejects_credentials_and_insecure_http():
    with pytest.raises(ValueError):
        gateway_config("https://user:password@example.com/v1")
    with pytest.raises(ValueError):
        gateway_config("http://example.com/v1")
