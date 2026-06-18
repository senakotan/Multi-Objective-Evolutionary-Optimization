from data.data_loader import load_dataset
from data.dri_loader import load_dri_for_user
from chromosome import create_random_chromosome
from decoder import decode_chromosome
from penalty import calculate_penalty
from data.user_preference_loader import load_user_preferences


def get_selected_foods(dataset, selected_food_ids):
    return dataset[dataset["id"].isin(selected_food_ids)].copy()


def calculate_total_user_preference(selected_food_ids, preference_dict):
    total_preference = 0.0

    for food_id in selected_food_ids:
        if food_id in preference_dict:
            total_preference += preference_dict[food_id]

    return total_preference


def calculate_objectives(
    decoded_menu,
    dataset,
    dri_df,
    user_id,
    penalty_weight=1.0
):
    selected_food_ids = decoded_menu["all_selected_foods"]
    selected_foods = get_selected_foods(dataset, selected_food_ids)

    preference_dict = load_user_preferences(user_id)

    total_preference = calculate_total_user_preference(
        selected_food_ids=selected_food_ids,
        preference_dict=preference_dict
    )

    total_cost = selected_foods["cost"].sum()
    total_time = selected_foods["totalTime"].sum()
    total_co2 = selected_foods["co2"].sum()

    distinct_group_count = selected_foods["foodGroupId"].nunique()

    penalty, violation_details = calculate_penalty(
        nutrient_totals=decoded_menu["nutrient_totals"],
        dri_df=dri_df
    )

    penalized_preference = total_preference - penalty_weight * penalty

    fitness = {
        "preference": total_preference,
        "cost": total_cost,
        "time": total_time,
        "co2": total_co2,
        "diversity": distinct_group_count,
        "penalty": penalty,
        "penalized_preference": penalized_preference,
        "violation_details": violation_details
    }

    return fitness


def print_fitness_report(fitness):
    print("\nFitness Report:")
    print(f"Preference: {fitness['preference']:.4f}")
    print(f"Cost: {fitness['cost']:.4f}")
    print(f"Time: {fitness['time']:.4f}")
    print(f"CO2: {fitness['co2']:.4f}")
    print(f"Diversity: {fitness['diversity']}")
    print(f"Penalty: {fitness['penalty']:.6f}")
    print(f"Penalized Preference: {fitness['penalized_preference']:.4f}")


if __name__ == "__main__":
    dataset = load_dataset()

    chromosome = create_random_chromosome(dataset)

    user_id = 1
    user_dri = load_dri_for_user(user_id)

    decoded_menu = decode_chromosome(
        chromosome=chromosome,
        dataset=dataset,
        dri_df=user_dri
    )

    fitness = calculate_objectives(
        decoded_menu=decoded_menu,
        dataset=dataset,
        dri_df=user_dri,
        user_id=user_id,
        penalty_weight=1.0
    )

    print_fitness_report(fitness)