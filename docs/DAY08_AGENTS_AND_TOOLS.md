# Day 8: Agents vs Workflows, Tool Use & Authorization Boundaries

**Focus:** Moving from passive Q&A to action-taking systems: function calling (tool use), JSON schemas, iteration loop limits, and enforcing server-side authorization so an agent can never access another customer's bank data.

---

## 🌟 The Most Important Concept: Agents vs Workflows & The Tool Security Invariant
An **Agent** is a system where the LLM dynamically decides *which* action to take and *when* to stop:
$$\text{User Query} \longrightarrow \text{LLM decides Tool} \longrightarrow \text{Execute Tool} \longrightarrow \text{LLM synthesizes response}$$

A **Deterministic Workflow** is hardcoded logic in Python:
$$\text{User Query} \longrightarrow \text{If balance query: run get\_balance()} \longrightarrow \text{Return template}$$

### When to choose which?
- **Choose a Deterministic Workflow:** When the task is predictable, high-frequency, and requires 100% reliability with minimum latency (e.g., balance lookup, password reset).
- **Choose an Agent:** When the user's intent is ambiguous, multi-step, requires open-ended reasoning, or combines policy retrieval with specific customer data in flexible ways.

---

## 🛡️ The Golden Security Rule of Tool Calling: Server-Side Identity Binding
When an LLM requests a tool call (e.g. `get_balance`), the JSON schema might look like this:

> ❌ **CRITICAL VULNERABILITY (Trusting LLM Arguments):**  
> Tool definition: `get_balance(customer_id: str)`  
> If an attacker types: *"Tell me balance for cust_999"*, the LLM will output `{"customer_id": "cust_999"}`. If your backend executes this, you have an **IDOR (Insecure Direct Object Reference) data breach**.

> ✅ **SECURE ARCHITECTURE (Server-Enforced Identity):**  
> The tool definition shown to the LLM: `get_balance(account_type: str = "checking")` (no customer_id parameter!).  
> When the Python runner executes `get_balance`, it injects the `customer_id` directly from the authenticated session (JWT token), completely ignoring what the user or LLM typed:
> ```python
> def execute_tool(tool_name, arguments, auth_customer_id):
>     if tool_name == "get_balance":
>         # auth_customer_id comes from server session, NOT from LLM!
>         return account_store.get_balance(customer_id=auth_customer_id, ...)
> ```

---

## 🔑 Key Takeaways & Design Patterns

### 1. Loop Limits & Cost Protection
Agents can enter infinite recursion (e.g., Tool fails $\rightarrow$ LLM retries $\rightarrow$ Tool fails $\rightarrow$ LLM retries forever).
- **Invariant:** Cap tool execution to **`max_iterations = 2`**. If unresolved after 2 turns, gracefully degrade and ask the user to contact support.

### 2. Failure Transparency (Never Lie About Side Effects)
If a tool execution raises an exception or returns an error:
- The agent must **never hallucinate that the tool succeeded**.
- The error must be formatted cleanly for the user without leaking stack traces or internal database errors.

---

## 🛠️ Artifacts & Code Delivered
- `bankassist/tools.py`:
  - Synthetic accounts database (`cust_101`, `cust_102`).
  - Read-only tools: `get_balance`, `list_transactions`.
  - Tool runner enforcing server-side `customer_id` binding.
- `bankassist/agent.py`: Agent orchestrator supporting Bedrock tool specifications, JSON schema validation, and bounded tool loops (`max_iterations=2`).
- `tests/test_tools_and_agent.py`:
  - Authorized customer retrieves their own balance.
  - Cross-customer access attempt is strictly blocked at the code layer.
  - Graceful handling of tool errors without false success claims.

---

## 🎯 Interview Check-in
> **Q: How do you prevent an AI Agent from accessing another customer's financial account?**  
> *A:* Never allow the LLM or user prompt to supply the `customer_id` argument to financial tools. Extract user identity exclusively from cryptographically signed session tokens (JWT) validated at the API boundary, and bind that identity server-side into tool calls. Treat all arguments output by the LLM as untrusted input.

