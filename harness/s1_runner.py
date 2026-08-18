#!/usr/bin/env python3
"""Compatibility entry point for S1.

Authoritative S1 evaluation is implemented by harness.confirmation_runner.
"""

from __future__ import annotations

import argparse

from contract.schema import ExperimentCell, Partition
from harness.confirmation_runner import run_cell


def run_s1(
    verbose: bool = True,
    gauntlet_filter: str | None = None,
    max_tasks: int | None = None,
    partition: Partition = Partition.DEV,
    task_file: str | None = None,
    seed: int = 0,
):
    if max_tasks is not None:
        raise ValueError(
            "max_tasks is not supported by the authoritative runner; use a frozen task file instead"
        )
    return run_cell(
        cell=ExperimentCell.S1,
        partition=partition,
        task_file=task_file,
        gauntlet_filter=gauntlet_filter,
        seed=seed,
        verbose=verbose,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognitive Core S1 runner")
    parser.add_argument("--partition", default="dev", choices=["dev", "replication", "lockbox"])
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--gauntlet", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run_s1(
        verbose=not args.quiet,
        gauntlet_filter=args.gauntlet,
        partition=Partition(args.partition),
        task_file=args.task_file,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
