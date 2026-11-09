from dataclasses import dataclass
from typing import Any
from bankassist.rag import RAGPipeline, RAGResult
from bankassist.tools import SecureToolRunner


@dataclass(frozen=True)
class AgentResult:
    text: str
    tool_called: str | None
    tool_success: bool
    is_abstention: bool


class BankAgent:
    """Agent that handles both policy RAG queries and authenticated tool calls,
    with iteration loop limits (max_iterations=2) and failure transparency.
    """

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        tool_runner: SecureToolRunner | None = None,
        max_iterations: int = 2,
    ):
        self.rag = rag_pipeline
        self.tool_runner = tool_runner or SecureToolRunner()
        self.max_iterations = max_iterations

    def run(
        self,
        question: str,
        authenticated_customer_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentResult:
        q_lower = question.lower()

        # Tool intent detection (simulating Bedrock toolUse block)
        if any(w in q_lower for w in ["balance", "funds", "how much money", "how much do i have"]):
            tool_name = "get_balance"
            account_type = "savings" if "savings" in q_lower else "checking"
            args = {"account_type": account_type}

            tool_output = self.tool_runner.execute_tool(
                tool_name=tool_name,
                arguments=args,
                authenticated_customer_id=authenticated_customer_id,
            )

            if not tool_output.get("success"):
                err_msg = tool_output.get("error", "Unable to retrieve balance.")
                return AgentResult(
                    text=f"I could not retrieve your balance: {err_msg}",
                    tool_called=tool_name,
                    tool_success=False,
                    is_abstention=True,
                )

            bal = tool_output["balance"]
            curr = tool_output["currency"]
            atype = tool_output["account_type"]
            return AgentResult(
                text=f"Your {atype} account balance is {bal:,.2f} {curr}.",
                tool_called=tool_name,
                tool_success=True,
                is_abstention=False,
            )

        elif any(w in q_lower for w in ["transactions", "recent charges", "history", "statement activity"]):
            tool_name = "list_transactions"
            tool_output = self.tool_runner.execute_tool(
                tool_name=tool_name,
                arguments={"limit": 5},
                authenticated_customer_id=authenticated_customer_id,
            )

            if not tool_output.get("success"):
                err_msg = tool_output.get("error", "Unable to list transactions.")
                return AgentResult(
                    text=f"I could not retrieve your transactions: {err_msg}",
                    tool_called=tool_name,
                    tool_success=False,
                    is_abstention=True,
                )

            tx_lines = [
                f"- {t['date']}: {t['description']} ({t['amount']:+.2f} credits)"
                for t in tool_output["transactions"]
            ]
            response_text = "Here are your recent transactions:\n" + "\n".join(tx_lines)
            return AgentResult(
                text=response_text,
                tool_called=tool_name,
                tool_success=True,
                is_abstention=False,
            )

        # Non-tool policy questions fall back to the safe RAG pipeline
        rag_res: RAGResult = self.rag.run(question, session_id=session_id)
        return AgentResult(
            text=rag_res.text,
            tool_called=None,
            tool_success=False,
            is_abstention=rag_res.is_abstention,
        )