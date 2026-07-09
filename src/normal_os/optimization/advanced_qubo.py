from typing import Any, Dict, Tuple
import dimod
import neal
import structlog

from normal_os.core.models import QUBOProblem, QUBOSolution

logger = structlog.get_logger(__name__)


class AdvancedQUBOSolver:
    """Advanced QUBO solver with multiple strategies (extracted + normalized from Horkrux QUBO suite)."""

    def __init__(self):
        self.neal_sampler = neal.SimulatedAnnealingSampler()
        self.cache: Dict[str, QUBOSolution] = {}

    def solve(
        self,
        problem: QUBOProblem,
        strategy: str = "neal",
        num_reads: int = 1000,
    ) -> QUBOSolution:
        problem_id = problem.id or self._make_id(problem)

        if problem_id in self.cache:
            return self.cache[problem_id]

        Q_full = dict(problem.Q)
        for i, b in problem.bias.items():
            Q_full[(i, i)] = Q_full.get((i, i), 0.0) + b

        bqm = dimod.BinaryQuadraticModel.from_qubo(Q_full)

        if strategy == "neal":
            response = self.neal_sampler.sample(bqm, num_reads=num_reads)
            best = response.first
            solution = QUBOSolution(
                problem_id=problem_id,
                solution={int(k): int(v) for k, v in best.sample.items()},
                energy=float(best.energy),
                num_reads=num_reads,
                solver="neal",
            )
        else:
            raise NotImplementedError(f"Strategy {strategy} not implemented")

        self.cache[problem_id] = solution
        return solution

    def _make_id(self, problem: QUBOProblem) -> str:
        import hashlib
        content = str(sorted(problem.Q.items())) + str(sorted(problem.bias.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:12]