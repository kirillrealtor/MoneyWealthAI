from app.ai.mock_provider import MockProvider


async def test_mock_provider_routing_and_formatting() -> None:
    async def fake_execute_tool(name: str, args: dict) -> tuple[str, bool]:
        if name == "get_spending_summary":
            return '{"total_spend": 123.45, "top_categories": [{"category": "FOOD", "amount": 123.45}]}', False
        elif name == "get_account_balances":
            payload = (
                '{"accounts": [{"name": "Check", "balance": 500.0, "type": "depository"}], '
                '"total_assets": 500.0, "total_debt": 0.0, "net_worth": 500.0}'
            )
            return payload, False
        return "{}", False

    provider = MockProvider()

    # Test spending intent routing
    res = await provider.run(
        system="",
        messages=[{"role": "user", "content": "where is my money going?"}],
        tools=[],
        execute_tool=fake_execute_tool,
    )
    assert res.provider == "mock"
    assert "get_spending_summary" in res.tool_calls_made
    assert "$123.45" in res.text
    assert "FOOD" in res.text

    # Test balance intent routing
    res2 = await provider.run(
        system="",
        messages=[{"role": "user", "content": "what is my net worth?"}],
        tools=[],
        execute_tool=fake_execute_tool,
    )
    assert "get_account_balances" in res2.tool_calls_made
    assert "$500.00" in res2.text
    assert "Check" in res2.text
