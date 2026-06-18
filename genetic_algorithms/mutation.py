"""
MODP için takas mutasyonu.
Her parçada pm olasılığıyla iki konum takas edilir.
Varsayılan oran: pm = 1 / n.
"""

import random
from typing import Optional

Chromosome = dict[str, list[int]]


def _swap_mutation_single(genes: list[int], pm: float) -> list[int]:

    mutated = genes[:]

    if len(mutated) < 2:
        return mutated

    if random.random() < pm:
        idx1, idx2 = random.sample(range(len(mutated)), 2)
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]

    return mutated


def swap_mutation(
    chromosome: Chromosome,
    pm_breakfast: Optional[float] = None,
    pm_lunch_dinner: Optional[float] = None,
) -> Chromosome:

    breakfast = chromosome["breakfast"]
    lunch_dinner = chromosome["lunch_dinner"]

    if pm_breakfast is None:
        pm_breakfast = 1.0 / max(len(breakfast), 1)

    if pm_lunch_dinner is None:
        pm_lunch_dinner = 1.0 / max(len(lunch_dinner), 1)

    mutated_breakfast = _swap_mutation_single(breakfast, pm_breakfast)
    mutated_lunch_dinner = _swap_mutation_single(lunch_dinner, pm_lunch_dinner)

    return {
        "breakfast": mutated_breakfast,
        "lunch_dinner": mutated_lunch_dinner,
    }


if __name__ == "__main__":

    print("=" * 55)
    print("mutation.py — self-test")
    print("=" * 55)

    BREAKFAST_IDS = list(range(1, 95))
    LUNCH_IDS = list(range(95, 406))

    def _make_chromosome(seed: int) -> Chromosome:
        b = BREAKFAST_IDS[:]
        ld = LUNCH_IDS[:]

        random.seed(seed)
        random.shuffle(b)
        random.shuffle(ld)

        return {
            "breakfast": b,
            "lunch_dinner": ld
        }

    original = _make_chromosome(7)

    print(f"\nOriginal — breakfast[:5]:     {original['breakfast'][:5]}")
    print(f"Original — lunch_dinner[:5]:  {original['lunch_dinner'][:5]}")

    mutated = swap_mutation(original)

    print(f"\nMutated  — breakfast[:5]:     {mutated['breakfast'][:5]}")
    print(f"Mutated  — lunch_dinner[:5]:  {mutated['lunch_dinner'][:5]}")

    def _validate(chrom: Chromosome, label: str) -> None:

        b_set = set(chrom["breakfast"])
        ld_set = set(chrom["lunch_dinner"])

        assert b_set == set(BREAKFAST_IDS), \
            f"{label}: breakfast IDs mismatch!"

        assert len(chrom["breakfast"]) == len(BREAKFAST_IDS), \
            f"{label}: breakfast has duplicate IDs!"

        assert ld_set == set(LUNCH_IDS), \
            f"{label}: lunch_dinner IDs mismatch!"

        assert len(chrom["lunch_dinner"]) == len(LUNCH_IDS), \
            f"{label}: lunch_dinner has duplicate IDs!"

        assert b_set.isdisjoint(ld_set), \
            f"{label}: cross-contamination between parts!"

        print(f"  {label} is a valid chromosome.")

    print("\nValidating mutated chromosome:")

    _validate(mutated, "Mutated chromosome")

    assert original["breakfast"][:5] == _make_chromosome(7)["breakfast"][:5], \
        "Original chromosome was modified!"

    print("  Original chromosome is unchanged (mutation works on copies).")

    print("\nForced swap test (pm=1.0 for both parts):")

    diff_b = 0
    diff_ld = 0

    for _ in range(100):
        c = _make_chromosome(42)

        m = swap_mutation(
            c,
            pm_breakfast=1.0,
            pm_lunch_dinner=1.0
        )

        if m["breakfast"] != c["breakfast"]:
            diff_b += 1

        if m["lunch_dinner"] != c["lunch_dinner"]:
            diff_ld += 1

    print(f"  Breakfast changed in 100/100 runs: {diff_b}/100")
    print(f"  Lunch/dinner changed in 100/100 runs: {diff_ld}/100")

    assert diff_b == 100, \
        "pm=1.0 should always trigger a breakfast swap!"

    assert diff_ld == 100, \
        "pm=1.0 should always trigger a lunch/dinner swap!"

    print("\nStress test: 500 mutations")

    for trial in range(500):
        base = _make_chromosome(trial)
        result = swap_mutation(base)
        _validate(result, f"Trial {trial}")

    print("All 500 mutation trials passed.")
