import os
import json
import pandas as pd

from data_loader import load_dataset
from dri_loader import load_dri_for_user
from nsga2 import run_nsga2
from spea2 import run_spea2


RESULTS_DIR = "results"

USERS = [1, 97]
ALGORITHMS = ["nsga2", "spea2"]
DIVERSITY_SETTINGS = [("div_on", True), ("div_off", False)]

POPULATION_SIZE = 20
GENERATIONS = 50
ARCHIVE_SIZE = 20

OBJECTIVES = ("cost", "time")
OBJECTIVE_NAMES = ["preference", "cost", "time"]

PENALTY_WEIGHT = 1.0
DIVERSITY_ALPHA = 0.5
PC = 0.9
SEED = 42

NUTRIENTS = ["energy", "protein", "carbohydrate", "fiber", "sodium"]


def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def get_penalty(fitness):
    return fitness.get("total_penalty", fitness["penalty"])


def dri_to_dict(dri_df):
    return {
        row["nutrient_name"]: {
            "RLL": float(row["RLL"]),
            "RUL": float(row["RUL"])
        }
        for _, row in dri_df.iterrows()
    }


def constraint_count(totals, dri_df):
    dri = dri_to_dict(dri_df)
    count = 0

    for nutrient in NUTRIENTS:
        value = float(totals[nutrient])
        if dri[nutrient]["RLL"] <= value <= dri[nutrient]["RUL"]:
            count += 1

    return count


def choose_three(pareto_front):
    if not pareto_front:
        return []

    best_preference = max(
        pareto_front,
        key=lambda x: x["fitness"]["preference"]
    )

    lowest_penalty = min(
        pareto_front,
        key=lambda x: get_penalty(x["fitness"])
    )

    balanced = min(
        pareto_front,
        key=lambda x: get_penalty(x["fitness"]) - 0.01 * x["fitness"]["preference"]
    )

    return [
        ("best_preference", best_preference),
        ("lowest_penalty", lowest_penalty),
        ("balanced", balanced)
    ]


def solution_row(solution, algorithm, user_id, diversity_label, solution_type, dri_df):
    fitness = solution["fitness"]
    decoded = solution["decoded_menu"]
    totals = decoded["nutrient_totals"]

    return {
        "algorithm": algorithm,
        "user_id": user_id,
        "diversity_label": diversity_label,
        "solution_type": solution_type,
        "preference": fitness["preference"],
        "cost": fitness["cost"],
        "time": fitness["time"],
        "co2": fitness["co2"],
        "diversity": fitness["diversity"],
        "penalty": get_penalty(fitness),
        "constraint_compliance_count": constraint_count(totals, dri_df),
        "breakfast": json.dumps(decoded["breakfast"]),
        "lunch_dinner": json.dumps(decoded["lunch_dinner"]),
        "all_selected_foods": json.dumps(decoded["all_selected_foods"]),
        **{n: totals[n] for n in NUTRIENTS}
    }


def nutrient_summary_row(solution, algorithm, user_id, diversity_label, solution_type, dri_df):
    fitness = solution["fitness"]
    totals = solution["decoded_menu"]["nutrient_totals"]
    dri = dri_to_dict(dri_df)

    row = {
        "algorithm": algorithm,
        "user_id": user_id,
        "diversity_label": diversity_label,
        "solution_type": solution_type,
        "preference": fitness["preference"],
        "cost": fitness["cost"],
        "time": fitness["time"],
        "co2": fitness["co2"],
        "diversity": fitness["diversity"],
        "penalty": get_penalty(fitness),
        "constraint_compliance_count": constraint_count(totals, dri_df)
    }

    for nutrient in NUTRIENTS:
        value = float(totals[nutrient])
        rll = dri[nutrient]["RLL"]
        rul = dri[nutrient]["RUL"]

        if value < rll:
            status = "LOW"
        elif value > rul:
            status = "HIGH"
        else:
            status = "OK"

        row[f"{nutrient}_value"] = value
        row[f"{nutrient}_RLL"] = rll
        row[f"{nutrient}_RUL"] = rul
        row[f"{nutrient}_status"] = status

    return row


def menu_rows(solution, algorithm, user_id, diversity_label, solution_type, dataset):
    decoded = solution["decoded_menu"]
    fitness = solution["fitness"]

    rows = []
    selected_foods = dataset[dataset["id"].isin(decoded["all_selected_foods"])]

    for _, food in selected_foods.iterrows():
        food_id = int(food["id"])

        rows.append({
            "algorithm": algorithm,
            "user_id": user_id,
            "diversity_label": diversity_label,
            "solution_type": solution_type,
            "meal_type": "breakfast" if food_id in decoded["breakfast"] else "lunch_dinner",
            "food_id": food_id,
            "food_name": food["name"],
            "food_group_id": food["foodGroupId"],
            "cost": food["cost"],
            "time": food["totalTime"],
            "co2": food["co2"],
            "energy": food["energy"],
            "protein": food["protein"],
            "carbohydrate": food["carbohydrate"],
            "fiber": food["fiber"],
            "sodium": food["sodium"],
            "solution_preference": fitness["preference"],
            "solution_penalty": get_penalty(fitness),
            "solution_diversity": fitness["diversity"]
        })

    return rows


def run_experiment(algorithm, user_id, diversity_label, use_diversity, dataset):
    print(f"\nRunning {algorithm.upper()} | User {user_id} | {diversity_label}")

    dri_df = load_dri_for_user(user_id)

    if algorithm == "nsga2":
        result = run_nsga2(
            dataset=dataset,
            dri_df=dri_df,
            user_id=user_id,
            population_size=POPULATION_SIZE,
            generations=GENERATIONS,
            objectives=OBJECTIVES,
            penalty_weight=PENALTY_WEIGHT,
            use_diversity=use_diversity,
            diversity_alpha=DIVERSITY_ALPHA,
            pc=PC,
            seed=SEED
        )

    elif algorithm == "spea2":
        result = run_spea2(
            dataset=dataset,
            user_id=user_id,
            population_size=POPULATION_SIZE,
            archive_size=ARCHIVE_SIZE,
            generations=GENERATIONS,
            objective_names=OBJECTIVE_NAMES,
            use_diversity=use_diversity,
            penalty_weight=PENALTY_WEIGHT,
            diversity_alpha=DIVERSITY_ALPHA,
            pc=PC,
            random_seed=SEED
        )

    else:
        raise ValueError("Unknown algorithm")

    return result, dri_df


def main():
    ensure_results_dir()
    dataset = load_dataset()

    pareto_rows = []
    history_rows = []
    sample_menu_rows = []
    nutrient_rows = []

    for algorithm in ALGORITHMS:
        for user_id in USERS:
            for diversity_label, use_diversity in DIVERSITY_SETTINGS:
                result, dri_df = run_experiment(
                    algorithm,
                    user_id,
                    diversity_label,
                    use_diversity,
                    dataset
                )

                pareto_front = result["pareto_front"]

                for i, solution in enumerate(pareto_front):
                    pareto_rows.append(
                        solution_row(
                            solution,
                            algorithm,
                            user_id,
                            diversity_label,
                            f"pareto_{i}",
                            dri_df
                        )
                    )

                for h in result["history"]:
                    row = h.copy()
                    row["algorithm"] = algorithm
                    row["user_id"] = user_id
                    row["diversity_label"] = diversity_label
                    history_rows.append(row)

                for solution_type, solution in choose_three(pareto_front):
                    nutrient_rows.append(
                        nutrient_summary_row(
                            solution,
                            algorithm,
                            user_id,
                            diversity_label,
                            solution_type,
                            dri_df
                        )
                    )

                    sample_menu_rows.extend(
                        menu_rows(
                            solution,
                            algorithm,
                            user_id,
                            diversity_label,
                            solution_type,
                            dataset
                        )
                    )

    pd.DataFrame(pareto_rows).to_csv(f"{RESULTS_DIR}/pareto_all.csv", index=False)
    pd.DataFrame(history_rows).to_csv(f"{RESULTS_DIR}/history_all.csv", index=False)
    pd.DataFrame(sample_menu_rows).to_csv(f"{RESULTS_DIR}/sample_menus.csv", index=False)
    pd.DataFrame(nutrient_rows).to_csv(f"{RESULTS_DIR}/sample_nutrient_summary.csv", index=False)

    print("\nSaved:")
    print("results/pareto_all.csv")
    print("results/history_all.csv")
    print("results/sample_menus.csv")
    print("results/sample_nutrient_summary.csv")


if __name__ == "__main__":
    main()