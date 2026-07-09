"""Practical QUBO solver wrapper using dimod.

Clean implementation suitable for task scheduling and prioritization.
"""

import dimod
import time
import numpy as np
from typing import Any

from ..core.models import OptimizationResult, Task


class QUBOSolver:
    """Solves QUBO problems for task ordering and resource allocation."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout or 5.0

    def optimize_task_order(self, tasks: list[Task]) -> OptimizationResult:
        """Optimize the execution order of tasks using a simple QUBO formulation."""
        if not tasks:
            return OptimizationResult(task_order=[], energy=0.0, solver_time_ms=0.0)

        start = time.perf_counter()

        n = len(tasks)
        # Simple QUBO: penalize high-priority tasks being placed late
        # and reward grouping tasks with similar capabilities
        Q = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    # Linear term: earlier position for higher priority
                    Q[i, i] = -tasks[i].priority * 10
                else:
                    # Interaction: small penalty for different capabilities
                    cap_i = set(tasks[i].required_capabilities)
                    cap_j = set(tasks[j].required_capabilities)
                    if cap_i.isdisjoint(cap_j):
                        Q[i, j] = 2.0

        # Solve with dimod ExactSolver (good for small instances, replace with Leap for production)
        bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
        sampler = dimod.ExactSolver()
        sampleset = sampler.sample(bqm)

        best_sample = sampleset.first.sample
        # Convert binary solution to ordering (simple heuristic)
        order_indices = sorted(range(n), key=lambda k: -best_sample.get(k, 0) * tasks[k].priority)
        task_order = [tasks[i].id for i in order_indices]

        solver_time = (time.perf_counter() - start) * 1000

        return OptimizationResult(
            task_order=task_order,
            energy=float(sampleset.first.energy),
            solver_time_ms=solver_time,
            metadata={"num_tasks": n, "solver": "dimod.ExactSolver"},
        )

    def solve_generic_qubo(self, Q: dict[tuple[int, int], float]) -> dict[str, Any]:
        """Solve a generic QUBO problem."""
        start = time.perf_counter()
        bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
        sampler = dimod.ExactSolver()
        sampleset = sampler.sample(bqm)
        solver_time = (time.perf_counter() - start) * 1000

        return {
            "best_energy": float(sampleset.first.energy),
            "best_sample": dict(sampleset.first.sample),
            "solver_time_ms": solver_time,
        }