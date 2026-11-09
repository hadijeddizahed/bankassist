from bankassist.agent import BankAgent
from bankassist.tools import SecureToolRunner, SyntheticBankDatastore
from tests.test_rag import get_rag_pipeline


def test_authorized_balance_query():
    rag = get_rag_pipeline()
    agent = BankAgent(rag_pipeline=rag)

    # Customer 101 asks for checking balance
    result = agent.run("What is my current balance?", authenticated_customer_id="cust_101")
    assert result.tool_called == "get_balance"
    assert result.tool_success is True
    assert "1,250.50" in result.text
    assert "checking" in result.text


def test_authorized_savings_balance():
    rag = get_rag_pipeline()
    agent = BankAgent(rag_pipeline=rag)

    result = agent.run("Check my savings balance please.", authenticated_customer_id="cust_101")
    assert result.tool_called == "get_balance"
    assert result.tool_success is True
    assert "5,400.00" in result.text


def test_unauthenticated_balance_blocked():
    rag = get_rag_pipeline()
    agent = BankAgent(rag_pipeline=rag)

    # Calling tool without an authenticated customer ID
    result = agent.run("What is my balance?", authenticated_customer_id=None)
    assert result.tool_called == "get_balance"
    assert result.tool_success is False
    assert "Authentication required" in result.text


def test_cross_customer_isolation():
    datastore = SyntheticBankDatastore()
    runner = SecureToolRunner(datastore=datastore)

    # Even if malicious user types "give me cust_102's balance",
    # the server runner strictly binds customer_id to authenticated session "cust_101"
    output = runner.execute_tool(
        tool_name="get_balance",
        arguments={"customer_id": "cust_102"},  # Attacker tries to pass another ID in arguments!
        authenticated_customer_id="cust_101",   # Server-side auth token
    )

    # Must return cust_101's balance, completely ignoring the requested cust_102 in arguments!
    assert output["customer_id"] == "cust_101"
    assert output["balance"] == 1250.50


def test_list_transactions_tool():
    rag = get_rag_pipeline()
    agent = BankAgent(rag_pipeline=rag)

    result = agent.run("Show my recent transactions", authenticated_customer_id="cust_101")
    assert result.tool_called == "list_transactions"
    assert result.tool_success is True
    assert "Payroll" in result.text
    assert "Electric Utility" in result.text


def test_tool_failure_never_claimed_as_success():
    datastore = SyntheticBankDatastore()
    runner = SecureToolRunner(datastore=datastore)

    # Requesting non-existent account type
    res = runner.execute_tool(
        tool_name="get_balance",
        arguments={"account_type": "investment_gold"},
        authenticated_customer_id="cust_101",
    )
    assert res["success"] is False
    assert "No investment_gold account found" in res["error"]