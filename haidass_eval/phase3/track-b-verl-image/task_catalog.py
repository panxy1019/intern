TASK_ALIASES = {
    "mmlu": "leaderboard|mmlu|0|0",
    "arc_easy": "lighteval|arc:easy|0|0",
    "arc_challenge": "leaderboard|arc:challenge|0|0",
    "winogrande": "leaderboard|winogrande|0|0",
    "openbookqa": "lighteval|openbookqa|0|0",
    "piqa": "lighteval|piqa|0|0",
    "hellaswag": "leaderboard|hellaswag|0|0",
}


def resolve_task(alias):
    try:
        return TASK_ALIASES[alias]
    except KeyError as exc:
        choices = ", ".join(sorted(TASK_ALIASES))
        raise ValueError(f"Unknown task alias {alias!r}; choose one of: {choices}") from exc
