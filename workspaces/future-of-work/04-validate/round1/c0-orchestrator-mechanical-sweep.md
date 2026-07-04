# Round 1 — Orchestrator Mechanical Sweep (L5 depth floor)

Date: 2026-07-04. Posture: L5_DELEGATED. Scope: `src/sequor/**` (SHIPPED comms-wedge). Platform specs are target-state (out of scope).

## Mechanical sweeps (literal command + actual output)

| Sweep                     | Command                                                                                                          | Output                                                                | Verdict                                                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| Stub/placeholder markers  | `grep -rnE "\b(TODO\|FIXME\|HACK\|XXX\|STUB)\b\|NotImplementedError" src/sequor --include='*.py'`                | count: 0                                                              | PASS                                                    |
| Fake/mock/simulated data  | `grep -rniE "simulated_\|fake_response\|dummy_\|MOCK_\|FAKE_\|DUMMY_\|placeholder_" src/sequor --include='*.py'` | (empty)                                                               | PASS                                                    |
| Raw SQL (f-string/concat) | `grep -rnE "(execute\|executemany)\(\s*f['\"]\|SELECT .*\{\|INSERT .*\+" src/sequor --include='*.py'`            | (empty)                                                               | PASS                                                    |
| Bare except               | `grep -rnE "except\s*:" src/sequor --include='*.py'`                                                             | count: 0                                                              | PASS                                                    |
| Hardcoded model strings   | `grep -rnE '"(gpt-[0-9]\|claude-[0-9]\|text-embedding-)' src/sequor --include='*.py'`                            | config.py:32 `openai_embedding_model: str = "text-embedding-3-small"` | ACCEPTABLE (pydantic-settings default, env-overridable) |
| Test collection           | `.venv/bin/python -m pytest --collect-only -q tests/`                                                            | 497 collected, 3 errors                                               | FAIL (see H-1)                                          |

## Findings

- **[HIGH] H-orch-1 — Hardcoded JWT secret fallback** — `src/sequor/auth.py:64` — `secret = settings.jwt_secret or "dev-secret-change-in-production"`. If `jwt_secret` env is unset/empty, JWTs are signed and verified with a publicly-known default → any attacker can forge valid operator tokens (auth bypass). Evidence: `sed -n '64p' src/sequor/auth.py`. Spec ref: security.md § "No Hardcoded Secrets". Fix: fail-fast at startup if `jwt_secret` unset in non-dev env (raise on empty in prod); never fall back to a literal signing key. (To be independently confirmed by security-reviewer.)

- **[HIGH] H-orch-2 — 3 integration tests fail collection** — `tests/integration/test_digest_integration.py`, `test_e2e_escalation_chain.py`, `test_e2e_happy_path.py` — `ImportError: cannot import name 'gather_digest_data' / 'format_digest_email' from 'sequor.digest.service'`. Whole integration suite blocked from collecting. Evidence: `pytest --collect-only` output above. (Owned by rt-c1-routing for root-cause: stale test vs missing impl.)

- **[LOW] L-orch-1 — JWT decode failure not logged** — `src/sequor/auth.py:68` `except JWTError: return None`. Documented contract (invalid→None) so acceptable per zero-tolerance Rule 3, but a debug-level log would aid auth-failure observability.

- **[WARN] W-orch-1 — StarletteDeprecationWarning** — `fastapi/testclient` uses `starlette.testclient` which warns "Using httpx with starlette.testclient is deprecated; install httpx2". Surfaced by the dep upgrade (httpx/starlette newer). Disposition: third-party deprecation; track for a follow-up (pin or migrate to httpx2 when fastapi/starlette support lands). Not blocking; log-triaged.

## Not findings (verified negative)

- `escalation/scheduler.py:50` `except asyncio.CancelledError: pass` — legitimate task-cancellation cleanup during `stop()`. Not a silent fallback.
- `config.py` LLM defaults (Ollama primary `llama3.1` / `nomic-embed-text`; OpenAI embedding fallback) — pydantic-settings defaults, env-overridable. Sanctioned pattern.
