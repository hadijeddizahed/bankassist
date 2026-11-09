from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Account:
    customer_id: str
    account_type: str  # "checking" or "savings"
    balance: float
    currency: str = "demo credits"


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    customer_id: str
    description: str
    amount: float
    date: str


class SyntheticBankDatastore:
    """Isolated, read-only synthetic banking ledger for testing."""

    def __init__(self):
        self._accounts: dict[tuple[str, str], Account] = {
            ("cust_101", "checking"): Account("cust_101", "checking", balance=1250.50),
            ("cust_101", "savings"): Account("cust_101", "savings", balance=5400.00),
            ("cust_102", "checking"): Account("cust_102", "checking", balance=320.00),
        }
        self._transactions: dict[str, list[Transaction]] = {
            "cust_101": [
                Transaction("TX-1", "cust_101", "Direct Deposit Payroll", 2000.00, "2026-11-01"),
                Transaction("TX-2", "cust_101", "Grocery Market", -85.20, "2026-11-03"),
                Transaction("TX-3", "cust_101", "Electric Utility Bill", -120.00, "2026-11-05"),
            ],
            "cust_102": [
                Transaction("TX-4", "cust_102", "Coffee Shop", -4.50, "2026-11-02"),
            ],
        }

    def get_balance(self, customer_id: str, account_type: str = "checking") -> dict[str, Any]:
        key = (customer_id, account_type.lower())
        account = self._accounts.get(key)
        if not account:
            return {
                "error": f"No {account_type} account found for customer.",
                "success": False,
            }
        return {
            "customer_id": customer_id,
            "account_type": account.account_type,
            "balance": account.balance,
            "currency": account.currency,
            "success": True,
        }

    def list_transactions(self, customer_id: str, limit: int = 5) -> dict[str, Any]:
        txs = self._transactions.get(customer_id, [])
        return {
            "customer_id": customer_id,
            "transactions": [
                {
                    "id": t.transaction_id,
                    "description": t.description,
                    "amount": t.amount,
                    "date": t.date,
                }
                for t in txs[:limit]
            ],
            "success": True,
        }


# Bedrock-compatible Tool Specifications (JSON Schema for tool use)
BANK_TOOLS_SPEC = [
    {
        "toolSpec": {
            "name": "get_balance",
            "description": "Retrieve the current balance of the authenticated customer's account.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "account_type": {
                            "type": "string",
                            "enum": ["checking", "savings"],
                            "description": "The type of account to query (default is checking).",
                        }
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "list_transactions",
            "description": "List recent transactions for the authenticated customer's account.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of transactions to return (max 10).",
                        }
                    },
                    "required": [],
                }
            },
        }
    },
]


class SecureToolRunner:
    """Enforces server-side authorization: customer_id is ALWAYS injected
    from the server session, NEVER taken from LLM arguments!
    """

    def __init__(self, datastore: SyntheticBankDatastore | None = None):
        self.datastore = datastore or SyntheticBankDatastore()

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        authenticated_customer_id: str | None,
    ) -> dict[str, Any]:
        # Boundary 1: Authentication required for tool execution
        if not authenticated_customer_id:
            return {
                "success": False,
                "error": "Authentication required. Please log in to view account data.",
            }

        # Boundary 2: Explicit tool dispatch with server-side customer_id binding
        if tool_name == "get_balance":
            account_type = arguments.get("account_type", "checking")
            return self.datastore.get_balance(
                customer_id=authenticated_customer_id,
                account_type=account_type,
            )
        elif tool_name == "list_transactions":
            limit = min(int(arguments.get("limit", 5)), 10)
            return self.datastore.list_transactions(
                customer_id=authenticated_customer_id,
                limit=limit,
            )
        else:
            return {
                "success": False,
                "error": f"Unknown or disallowed tool: {tool_name}",
            }