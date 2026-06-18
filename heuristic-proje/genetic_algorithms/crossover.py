"""
MODP genetik algoritması için Sıralı Çaprazlama (OX).

Kromozomun iki bölümü ayrı çaprazlanır:
  - Her bölümde ID tekrarı olmaz.
  - ID'ler bölüm değiştirmez.

Tek bölüm için OX:
  1. İki kesme noktası seçilir.
  2. Orta parça bir ebeveynden alınır.
  3. Kalan yerler diğer ebeveyn sırasıyla doldurulur.
  4. İkinci çocuk simetrik üretilir.
"""

import random

Chromosome = dict[str, list[int]]


def _ox_single(parent1: list[int], parent2: list[int]) -> tuple[list[int], list[int]]:

    n = len(parent1)

    i, j = sorted(random.sample(range(n), 2))

    def _build_child(p_middle: list[int], p_fill: list[int]) -> list[int]:

        middle_segment = p_middle[i: j + 1]
        middle_set = set(middle_segment)

        fill_order = [
            gene
            for gene in (p_fill[j + 1:] + p_fill[: j + 1])
            if gene not in middle_set
        ]

        child: list[int] = [0] * n

        for k, gene in enumerate(middle_segment):
            child[i + k] = gene

        fill_positions = [
            (j + 1 + k) % n
            for k in range(n - len(middle_segment))
        ]

        for pos, gene in zip(fill_positions, fill_order):
            child[pos] = gene

        return child

    child1 = _build_child(parent1, parent2)
    child2 = _build_child(parent2, parent1)

    return child1, child2


def order_crossover(
    parent1: Chromosome,
    parent2: Chromosome,
    pc: float = 0.9,
) -> tuple[Chromosome, Chromosome]:

    if random.random() > pc:
        child1: Chromosome = {
            "breakfast": parent1["breakfast"][:],
            "lunch_dinner": parent1["lunch_dinner"][:]
        }

        child2: Chromosome = {
            "breakfast": parent2["breakfast"][:],
            "lunch_dinner": parent2["lunch_dinner"][:]
        }

        return child1, child2

    b_child1, b_child2 = _ox_single(
        parent1["breakfast"],
        parent2["breakfast"]
    )

    ld_child1, ld_child2 = _ox_single(
        parent1["lunch_dinner"],
        parent2["lunch_dinner"]
    )

    child1 = {
        "breakfast": b_child1,
        "lunch_dinner": ld_child1
    }

    child2 = {
        "breakfast": b_child2,
        "lunch_dinner": ld_child2
    }

    return child1, child2


if __name__ == "__main__":

    print("=" * 55)
    print("crossover.py — self-test")
    print("=" * 55)

    BREAKFAST_IDS = list(range(1, 95))
    LUNCH_IDS = list(range(95, 406))

    def _make_parent(seed: int) -> Chromosome:
        b = BREAKFAST_IDS[:]
        ld = LUNCH_IDS[:]

        random.seed(seed)
        random.shuffle(b)
        random.shuffle(ld)

        return {
            "breakfast": b,
            "lunch_dinner": ld
        }

    p1 = _make_parent(42)
    p2 = _make_parent(99)

    print(f"\nParent 1 — breakfast[:5]: {p1['breakfast'][:5]}")
    print(f"Parent 2 — breakfast[:5]: {p2['breakfast'][:5]}")

    child1, child2 = order_crossover(p1, p2, pc=0.9)

    print(f"\nChild 1  — breakfast[:5]: {child1['breakfast'][:5]}")
    print(f"Child 2  — breakfast[:5]: {child2['breakfast'][:5]}")

    def _validate(chrom: Chromosome, label: str) -> None:

        b_set = set(chrom["breakfast"])
        ld_set = set(chrom["lunch_dinner"])

        assert b_set == set(BREAKFAST_IDS), \
            f"{label}: breakfast IDs mismatch (expected {len(BREAKFAST_IDS)}, " \
            f"got {len(b_set)})"

        assert len(chrom["breakfast"]) == len(BREAKFAST_IDS), \
            f"{label}: breakfast has duplicates!"

        assert ld_set == set(LUNCH_IDS), \
            f"{label}: lunch_dinner IDs mismatch"

        assert len(chrom["lunch_dinner"]) == len(LUNCH_IDS), \
            f"{label}: lunch_dinner has duplicates!"

        assert b_set.isdisjoint(ld_set), \
            f"{label}: IDs shared between breakfast and lunch_dinner!"

        print(f"  {label} is a valid chromosome.")

    print("\nValidating offspring:")

    _validate(child1, "Child 1")
    _validate(child2, "Child 2")

    c1_nc, c2_nc = order_crossover(p1, p2, pc=0.0)

    assert c1_nc["breakfast"] == p1["breakfast"], \
        "No-crossover: child1 != parent1"

    assert c2_nc["breakfast"] == p2["breakfast"], \
        "No-crossover: child2 != parent2"

    print("\nNo-crossover branch: children are exact copies of parents.")

    print("\nRunning 100 crossovers for stress testing...")

    for trial in range(100):
        c1, c2 = order_crossover(p1, p2, pc=0.9)
        _validate(c1, f"Trial {trial} — Child 1")
        _validate(c2, f"Trial {trial} — Child 2")

    print("All 100 crossover trials passed.")