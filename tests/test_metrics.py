from discoverybrief.metrics import UsageLedger


def test_zero_is_preserved_and_missing_usage_stays_unknown():
    ledger = UsageLedger()
    ledger.record_model({"prompt_tokens": 0, "completion_tokens": 0})
    assert ledger.summary()["llm_input_tokens"] == 0
    assert ledger.summary()["usage_complete"] is True
    ledger.record_model(None)
    summary = ledger.summary()
    assert summary["llm_input_tokens"] is None
    assert summary["llm_output_tokens"] is None
    assert summary["estimated_model_cost_microusd"] is None
    assert summary["usage_complete"] is False


def test_reported_credits_do_not_hide_missing_values():
    ledger = UsageLedger()
    ledger.record_tavily(0)
    assert ledger.summary()["tavily_credits_reported"] == 0
    ledger.record_tavily(None)
    assert ledger.summary()["tavily_credits_reported"] is None
