# PROT-03: Prompts, AI Orchestration & Model Secret Exposure Audit

**Document:** 05_PROMPT_AND_MODEL_EXPOSURE.md  
**Audit Scope:** System instructions, prompt templates, few-shot exemplars, model-routing logic, and AI provider credentials.  

---

## 1. Proprietary AI Artifacts & Trade Secret Value

In modern document intelligence systems, system prompts, verification chain templates, and model-routing heuristics constitute significant intellectual property:
1. **Verification Prompt Chains:** Multi-step prompts that enforce strict negative constraints ("Abstain if evidence is insufficient", "Cite exact verbatim coordinate offsets").
2. **Contradiction Detection Heuristics:** Prompts designed to extract numerical claims and invariant relations from heterogeneous document formats.
3. **Adaptive Model Routing:** Algorithms determining when to invoke fast lightweight models (e.g., Claude 3.5 Haiku / GPT-4o-mini) versus heavy reasoning engines (e.g., Claude 3.5 Sonnet / o1).

**Distributing prompt templates or routing rules in client bundles permits competitors to duplicate AEGIS's extraction behavior without developing the underlying infrastructure.**

---

## 2. Model Credentials & Secret Isolation

### A. Provider API Keys
- The repository interacts with OpenAI (`OPENAI_API_KEY`) and Anthropic (`ANTHROPIC_API_KEY`).
- **Audit Rule:** Provider keys must **NEVER** be compiled into frontend JavaScript or included in downloadable Docker images.
- **Physical Boundary Enforcement:**
  - In the downloadable package, neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` is referenced.
  - The local `compose.yaml` contains no LLM environment variables.
  - All AI queries flow from the local proxy to the central Evaluation Gateway.
  - The Gateway injects cloud provider secrets held in secure cloud vaults (AWS Secrets Manager / GCP Secret Manager) when calling LLM endpoints.

---

## 3. System Prompt & Instruction Isolation

### A. Client-Side Presentation vs. Server-Side Execution
- **What the Client Sees:** Evaluators see user-facing questions, streaming tokens, finalized answer text, and clickable citation badges with confidence scores.
- **What Remains Private:**
  - Base system prompts;
  - Few-shot ground-truth exemplars;
  - Chain-of-thought verification steps;
  - Internal abstention threshold calculations.

### B. Static Bundle Inspection
Static analysis of all client JavaScript files in `web/` confirmed that zero base system prompts, provider keys, or LLM routing configurations are present in client assets (verified by `IP-TEST-004` and `IP-TEST-007`).
