import random
from typing import Any

Chromosome = dict[str, list[int]]
FitnessScore = dict[str, Any]


def binary_tournament_selection(
    population: list[Chromosome],
    fitness_scores: list[FitnessScore],
    tournament_size: int = 2,
) -> Chromosome:

    if not population:
        raise ValueError("Population must not be empty.")

    if len(population) != len(fitness_scores):
        raise ValueError(
            f"population ({len(population)}) and fitness_scores "
            f"({len(fitness_scores)}) must have the same length."
        )

    k = min(tournament_size, len(population))

    candidates_idx = random.sample(range(len(population)), k)

    best_idx = max(
        candidates_idx,
        key=lambda i: fitness_scores[i]["penalized_preference"]
    )

    return population[best_idx]


def select_mating_pool(
    population: list[Chromosome],
    fitness_scores: list[FitnessScore],
    pool_size: int,
    tournament_size: int = 2,
) -> list[Chromosome]:

    return [
        binary_tournament_selection(population, fitness_scores, tournament_size)
        for _ in range(pool_size)
    ]


def _pymoo_comp_by_penalized_preference(pop, P, **kwargs):  # type: ignore[no-untyped-def]

    import numpy as np  # type: ignore

    S = np.full(P.shape[0], np.nan)

    for i, (a, b) in enumerate(P):
        fa = pop[a].F[0]
        fb = pop[b].F[0]
        S[i] = a if fa <= fb else b

    return S.astype(int)


if __name__ == "__main__":

    print("=" * 55)
    print("selection.py — self-test")
    print("=" * 55)

    def _mock_chromosome(seed: int) -> Chromosome:
        breakfast_ids = list(range(1, 95))
        lunch_ids = list(range(95, 406))

        random.seed(seed)
        random.shuffle(breakfast_ids)
        random.shuffle(lunch_ids)

        return {
            "breakfast": breakfast_ids,
            "lunch_dinner": lunch_ids
        }

    pop_size = 10
    mock_pop = [_mock_chromosome(i) for i in range(pop_size)]

    mock_fitness = [
        {"penalized_preference": random.uniform(-5.0, 20.0)}
        for _ in range(pop_size)
    ]

    print("\nFitness scores assigned to population:")

    for idx, fs in enumerate(mock_fitness):
        print(
            f"  Individual {idx:>2}: penalized_preference = "
            f"{fs['penalized_preference']:.4f}"
        )

    winner = binary_tournament_selection(mock_pop, mock_fitness)

    winner_idx = mock_pop.index(winner)

    print(
        f"\nSingle tournament winner → Individual {winner_idx} "
        f"(score={mock_fitness[winner_idx]['penalized_preference']:.4f})"
    )

    pool = select_mating_pool(
        mock_pop,
        mock_fitness,
        pool_size=6
    )

    print(f"\nMating pool of size 6 selected.")

    for idx, ind in enumerate(pool):
        ind_idx = mock_pop.index(ind)

        print(
            f"  Slot {idx}: Individual {ind_idx} "
            f"(score={mock_fitness[ind_idx]['penalized_preference']:.4f})"
        )

    for ind in pool:
        assert set(ind["breakfast"]) == set(range(1, 95))
        assert set(ind["lunch_dinner"]) == set(range(95, 406))

    print("\n✓ All chromosome structures intact after selection.")

