"""
Menüdeki farklı besin grubu sayısına göre çeşitlilik cezası hesaplar.

Formül:
    diversity_penalty = alpha * (1.0 / distinct_group_count)

Grup azaldıkça ceza artar.
"""

import pandas as pd


def calculate_diversity_penalty(
    selected_foods_df: pd.DataFrame,
    alpha: float = 0.5
) -> tuple[float, int]:

    if selected_foods_df.empty or "foodGroupId" not in selected_foods_df.columns:
        return alpha * 1.0, 0

    distinct_group_count: int = int(
        selected_foods_df["foodGroupId"].nunique()
    )

    if distinct_group_count == 0:
        return alpha * 1.0, 0

    penalty: float = alpha * (1.0 / distinct_group_count)

    return penalty, distinct_group_count


if __name__ == "__main__":

    print("=" * 55)
    print("diversity.py — self-test")
    print("=" * 55)

    mock_data = {
        "id": list(range(1, 21)),
        "name": [f"Food_{i}" for i in range(1, 21)],
        "foodGroupId": [((i - 1) % 6) + 1 for i in range(1, 21)],
    }

    mock_df = pd.DataFrame(mock_data)

    penalty, groups = calculate_diversity_penalty(
        mock_df,
        alpha=0.5
    )

    print(
        f"\nMock menu with {len(mock_df)} items "
        f"across {groups} food groups"
    )

    print(
        f"Diversity penalty (alpha=0.5): "
        f"{penalty:.6f}"
    )

    single_group_df = mock_df.copy()
    single_group_df["foodGroupId"] = 3

    penalty2, groups2 = calculate_diversity_penalty(
        single_group_df,
        alpha=0.5
    )

    print(
        f"\nSingle-group menu: "
        f"{groups2} group → penalty={penalty2:.6f}"
    )

    empty_df = pd.DataFrame(
        columns=["id", "name", "foodGroupId"]
    )

    penalty3, groups3 = calculate_diversity_penalty(
        empty_df,
        alpha=0.5
    )

    print(
        f"\nEmpty menu: "
        f"{groups3} groups → penalty={penalty3:.6f}"
    )

    print("\nPenalty vs. distinct group count (alpha=0.5):")

    for n in [1, 2, 3, 4, 6, 8, 12, 18]:
        p = 0.5 * (1.0 / n)

        print(
            f"  {n:>3} groups → penalty = {p:.6f}"
        )