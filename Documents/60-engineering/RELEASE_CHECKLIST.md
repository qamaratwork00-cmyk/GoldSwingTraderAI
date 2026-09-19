# GoldSwingTraderAI — Release Checklist

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-release-gate  
**Authority:** Ordered release preparation and sign-off

## 1. How to use this checklist

This checklist is a gate, not a progress diary. Each item must be marked
PASS, FAIL, BLOCKED or NOT APPLICABLE with evidence. “The code looks ready” is
not a release result.

The release owner must preserve the commit, configuration class, test output
and evidence package used for the decision.

## 2. Release path

~~~mermaid
flowchart TB
    DOCS["Documents and contracts"] --> CODE["Code and dependency checks"]
    CODE --> TESTS["Deterministic test suite"]
    TESTS --> READINESS["READINESS runtime"]
    READINESS --> DEMO["DEMO certification"]
    DEMO --> RECOVERY["Restore and failover"]
    RECOVERY --> AUDIT["Final release audit"]
    AUDIT --> RELEASE["Release or block"]
~~~

## 3. Documentation gate

- [ ] Documents/README.md describes the manual set and authority rule.
- [ ] Every substantive Documents file has Status, Version and Authority.
- [ ] The documentation standard is frozen and the affected graph is updated.
- [ ] Phase 1–9, Phase 10, Phase 11 and Phase 12 remain separate.
- [ ] Architecture, floor wiring, runtime startup and persistent loop diagrams
      are present.
- [ ] Every production source module, script and test file appears in the
      file/test catalog.
- [ ] DEMO Guard, dashboard, recovery, backups and AI/ChatGPT boundaries are
      explained.
- [ ] No old document was silently erased or rewritten as part of the new
      manual.
- [ ] Local links, Mermaid fences and document metadata pass the manual
      verifier.

## 4. Code and dependency gate

- [ ] The intended Git revision is clean and recorded.
- [ ] The supported Python version is installed.
- [ ] Editable installation with required extras succeeds.
- [ ] Dependency versions are resolved and recorded.
- [ ] Ruff and the configured static checks pass.
- [ ] Secret scanning passes for source, logs, backup candidates and staged
      public artifacts.
- [ ] No code path bypasses the single broker-write boundary.
- [ ] No research or dashboard module can authorize a broker write.

## 5. Deterministic test gate

- [ ] Full pytest suite passes on the intended revision.
- [ ] Negative safety tests are present and pass.
- [ ] Runtime startup and readiness tests pass.
- [ ] Persistence, checkpoint, backup and restore tests pass.
- [ ] Controller fencing and SQLite coordination tests pass.
- [ ] Research evidence and promotion tests pass.
- [ ] The exact command and output are retained in the evidence package.

## 6. READINESS runtime gate

- [ ] MT5 initializes or the failure is visible with a stable reason.
- [ ] Account mode is DEMO.
- [ ] Account identity and server match the approved configuration.
- [ ] Preferred symbol resolves to the approved symbol.
- [ ] The runtime reads account, quote, completed candles and open positions.
- [ ] Stale market data keeps the process alive when keep-alive is enabled.
- [ ] Stale market data disables broker writes and exposes the reason.
- [ ] The dashboard renders the current readiness/recovery/controller facts.
- [ ] Runtime shutdown leaves durable state consistent.

## 7. DEMO broker gate

This gate requires a real approved DEMO account. It is not satisfied by mocks.

- [ ] DEMO Guard passes for the intended account and server.
- [ ] One controlled OPEN is observed and broker-verified.
- [ ] The returned ticket/order identity is stored.
- [ ] One controlled MODIFY is observed and broker-verified.
- [ ] The resulting stop/target state is reconciled with broker truth.
- [ ] One controlled CLOSE is observed and broker-verified.
- [ ] No duplicate write occurs after an uncertain acknowledgement.
- [ ] Spread, drift, volume, margin and ownership checks are evidenced.
- [ ] Logs contain no credentials or secret material.
- [ ] The operation is performed only in the declared DEMO scope.

## 8. Recovery and continuity gate

- [ ] A checkpoint is created from a known runtime state.
- [ ] A fresh database can be restored without changing broker truth.
- [ ] Broker positions are reconciled after restart.
- [ ] Unknown positions are not treated as empty exposure.
- [ ] A stale or corrupt checkpoint blocks unsafe continuation.
- [ ] The primary controller cannot be duplicated while its lease is valid.
- [ ] A stale primary cannot write after fencing.
- [ ] A standby can take over only after the coordination policy permits it.
- [ ] Recovery evidence records the before/after identities and timestamps.

## 9. Research gate

- [ ] The dataset has source, symbol, timezone, time range and fingerprint.
- [ ] Replay uses closed candles and no lookahead.
- [ ] Spread/slippage and management assumptions are explicit.
- [ ] Walk-forward and holdout boundaries are explicit.
- [ ] Metrics include risk, drawdown, affordability and execution friction.
- [ ] Discovery/invention candidates remain candidates until promotion.
- [ ] A promoted rule has an immutable evidence package and rollback path.
- [ ] No research result silently changes live production policy.

## 10. Final operator gate

- [ ] Setup and run instructions work on the target Windows machine.
- [ ] The user manual explains closed-market behaviour and stale-data waiting.
- [ ] The dashboard explains every actionable block in plain language.
- [ ] Backup publication is verified and contains no secrets.
- [ ] A release note states what was verified and what remains external.
- [ ] The final audit is signed by the release owner.

## 11. Release outcomes

| Outcome | Meaning |
|---|---|
| RELEASED | All mandatory gates for the declared scope pass |
| RELEASED-DEMO-OBSERVATION | Read-only DEMO observation passed; broker writes remain unverified |
| BLOCKED | A mandatory gate failed or evidence is missing |
| PARTIAL | Core tests pass but external/runtime proof remains pending |

The release label must name the scope. Do not call a PARTIAL result “project
complete”.
