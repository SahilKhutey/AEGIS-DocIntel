# LLM Provider & External Service Isolation (DEP-06)

## Security Invariants
1. **Server-Side Credentials:** Provider API keys (`AEGIS_OPENAI_API_KEY`, `AEGIS_ANTHROPIC_API_KEY`) are stored in server secret managers and never distributed to client artifacts (`DEP-TEST-010`).
2. **Client Key Injection Denied:** Evaluators cannot supply arbitrary provider keys or redirect outbound endpoints.
3. **Outbound Endpoint Whitelist:** Only approved model endpoints (`api.openai.com`, `api.anthropic.com`) are permitted.
4. **Proprietary Prompt Protection:** Private system reasoning frameworks remain server-side; errors redact keys and system prompts.
