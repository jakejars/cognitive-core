# Supervisor Architecture — Trust Boundary for Protocol Enforcement

## The Problem

The research agent that the contract constrains also has write access to the
contract/invariants, transition, and schema files. This is a trust boundary
violation: the agent could modify the verifier that decides whether its own
claims are valid.

## The Solution

The `contract/` package is designed as a **separate trust domain** from the
research agent workspace. In production, it should be deployed as:

### Option 1: Read-Only Mount (Recommended for DSH/Local)

```bash
# Mount contract/ as read-only before starting the research agent
chmod -R a-w /path/to/project/contract/
# The researcher workspace remains writable
chmod -R u+w /path/to/project/harness/ /path/to/project/ledger/
```

The research agent process runs with filesystem permissions that prevent it
from modifying `contract/`. It can still write to `ledger/`, `harness/`, etc.

### Option 2: Separate Git Repository (Recommended for CI/CD)

```text
cognitive-core-protocol/   ← separate repo, pinned to known hash
    contract/
        schema.py
        invariants.py
        transition.py
        receipt_writer.py
        adapters/
        tests/

cognitive-core-workspace/  ← research agent workspace
    harness/
    substrate/
    gauntlets/
    ledger/
    models/
```

The protocol repo is installed as a dependency (e.g., `pip install -e ../cognitive-core-protocol`).
The research agent cannot modify it without a separate PR and review.

### Option 3: Supervisor Sidecar Process

```text
┌─────────────────────────────┐     ┌──────────────────────────────┐
│ RESEARCH AGENT              │     │ SUPERVISOR (separate process)│
│                             │     │                              │
│  ReceiptWriter.write_run()  │────→│  verify_receipt_hash()       │
│  ClaimTransitioner          │────→│  verify_all()                │
│    .request_transition()    │     │  verify_transition()         │
└─────────────────────────────┘     └──────────────────────────────┘
```

The supervisor runs as a separate process with its own filesystem mount.
It exposes a minimal API (e.g., via stdin/stdout JSON-RPC or a Unix socket).
The research agent calls the supervisor but cannot modify it.

## Current Implementation

The `contract/` package already enforces the trust boundary programmatically:

1. **`ReceiptWriter`** is the only way to create experiment receipts.
   Runners cannot write receipt files directly.

2. **`ClaimTransitioner.request_transition()`** verifies `from_state` against
   `get_entity_state()`. A caller cannot spoof a state they haven't reached.

3. **`_receipts()`** in `invariants.py` recomputes the cryptographic hash of
   every loaded receipt. Tampered hashes are silently rejected.

4. **`check_lockbox_intact()`** and **`check_lockbox_pass()`** are separate
   checks. LOCKBOX_PASS requires both the lockbox to be uncontaminated AND
   the experiment to have been conducted with results.

5. **Tiered evidence**: DEV → REPLICATION → LOCKBOX transitions each require
   receipts at that specific tier. SUPPORTED_CLAIM requires all three.

## What the Supervisor Does NOT Do (Yet)

- **Filesystem-level isolation**: The `contract/` directory is currently writable
  by the research agent. A determined agent could modify the invariants.
  This is acceptable for the DEV/feasibility phase but must be addressed
  before the confirmation campaign produces final claims.

- **Process-level isolation**: The supervisor is not yet a separate process.
  The `contract/` package runs in-process with the harness. This means a bug
  in the harness could corrupt the contract state.

## Deployment Checklist

Before the confirmation campaign produces final claims:

- [x] `contract/` directory is read-only to the research agent process
      (local M5 Pro: `chmod -R a-w contract/`; verified write-denied and
      imports/`pytest`/`check-invariants.py` still pass)
- [x] `ledger/` directory is writable but its receipts are cryptographically
      verified on every load
- [x] The research agent's Python path does not include a writable directory
      that shadows `contract/` (verified `contract.__file__` resolves to the
      read-only repo package)
- [~] CI/CD pipeline: `protocol-tests.yml` runs compileall + pytest on PR;
      the full `check-invariants.py` gate is executed locally before any claim
      (CI cannot run model/tokenizer checks without the local checkpoints)
- [x] The `contract/` package hash is pinned in `ledger/confirmation-record.json`
      (contract tree SHA-256 + git HEAD + adapter revisions/hashes)

## Current Status (confirmation campaign)

- DEV + REPLICATION matrices complete with validated receipts.
- LOCKBOX plaintext held outside the repo (`/Users/jake/cognitive-core-lockbox/`,
  mode 600); ledger frozen with hashes; release not authorised until the
  supervisor boundary above was in place.
- Phase D counterfactual gate and Phase C LCTX curve remain open items.