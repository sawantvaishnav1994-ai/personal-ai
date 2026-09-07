from __future__ import annotations

from tools.registry import Risk, Tool


def register(reg, benchmark):
    reg.register(
        Tool(
            'capability_benchmark',
            'Run the Personal AI P2 capability benchmark; params: capability or all',
            lambda p: benchmark.run_all()
            if str(p.get('capability', 'all')).lower() == 'all'
            else benchmark.run(str(p['capability'])),
            Risk.READ_ONLY,
        )
    )
    reg.register(
        Tool(
            'capability_task_matrix',
            'Read the permanent competitive task evidence matrix',
            lambda p: benchmark.task_matrix(),
            Risk.READ_ONLY,
        )
    )
