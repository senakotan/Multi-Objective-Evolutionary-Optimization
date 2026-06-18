from data.data_loader import load_dataset
from data.dri_loader import load_dri_for_user
from chromosome import create_random_chromosome


NUTRIENT_COLUMNS = [
    "energy",
    "protein",
    "carbohydrate",
    "fiber",
    "sodium"
]


def convert_dri_to_dict(dri_df):
    dri_dict = {}

    for _, row in dri_df.iterrows():
        nutrient_name = row["nutrient_name"]

        dri_dict[nutrient_name] = {
            "RLL": float(row["RLL"]),
            "RUL": float(row["RUL"])
        }

    return dri_dict


def initialize_totals():
    return {
        "energy": 0.0,
        "protein": 0.0,
        "carbohydrate": 0.0,
        "fiber": 0.0,
        "sodium": 0.0
    }


def add_food_to_totals(totals, food_row):
    new_totals = totals.copy()

    for nutrient in NUTRIENT_COLUMNS:
        new_totals[nutrient] += float(food_row[nutrient])

    return new_totals


def exceeds_limit(totals, dri_dict, nutrients_to_check, multiplier=1.15):
    for nutrient in nutrients_to_check:
        upper_limit = dri_dict[nutrient]["RUL"] * multiplier

        if totals[nutrient] > upper_limit:
            return True

    return False


def satisfies_lower_limit(totals, dri_dict, nutrients_to_check, multiplier=0.90):
    for nutrient in nutrients_to_check:
        lower_limit = dri_dict[nutrient]["RLL"] * multiplier

        if totals[nutrient] < lower_limit:
            return False

    return True


def get_food_by_id(dataset, food_id):
    food_row = dataset[dataset["id"] == food_id]

    if food_row.empty:
        return None

    return food_row.iloc[0]


def decode_breakfast(chromosome, dataset, dri_dict):
    selected_breakfast = []
    totals = initialize_totals()

    breakfast_nutrients = ["energy", "protein"]

    breakfast_dri = {}

    for nutrient in NUTRIENT_COLUMNS:
        breakfast_dri[nutrient] = {
            "RLL": dri_dict[nutrient]["RLL"] * 0.35,
            "RUL": dri_dict[nutrient]["RUL"] * 0.35
        }

    for food_id in chromosome["breakfast"]:
        food_row = get_food_by_id(dataset, food_id)

        if food_row is None:
            continue

        tentative_totals = add_food_to_totals(totals, food_row)

        if exceeds_limit(
            tentative_totals,
            breakfast_dri,
            breakfast_nutrients,
            multiplier=1.15
        ):
            continue

        selected_breakfast.append(food_id)
        totals = tentative_totals

        if satisfies_lower_limit(
            totals,
            breakfast_dri,
            breakfast_nutrients,
            multiplier=0.90
        ):
            break

    return selected_breakfast, totals


def decode_lunch_dinner(chromosome, dataset, dri_dict, current_totals):
    selected_lunch_dinner = []
    totals = current_totals.copy()

    for food_id in chromosome["lunch_dinner"]:
        food_row = get_food_by_id(dataset, food_id)

        if food_row is None:
            continue

        tentative_totals = add_food_to_totals(totals, food_row)

        if exceeds_limit(
            tentative_totals,
            dri_dict,
            NUTRIENT_COLUMNS,
            multiplier=1.15
        ):
            continue

        selected_lunch_dinner.append(food_id)
        totals = tentative_totals

        if satisfies_lower_limit(
            totals,
            dri_dict,
            NUTRIENT_COLUMNS,
            multiplier=0.90
        ):
            break

    return selected_lunch_dinner, totals


def decode_chromosome(chromosome, dataset, dri_df):
    dri_dict = convert_dri_to_dict(dri_df)

    breakfast_menu, breakfast_totals = decode_breakfast(
        chromosome=chromosome,
        dataset=dataset,
        dri_dict=dri_dict
    )

    lunch_dinner_menu, final_totals = decode_lunch_dinner(
        chromosome=chromosome,
        dataset=dataset,
        dri_dict=dri_dict,
        current_totals=breakfast_totals
    )

    decoded_menu = {
        "breakfast": breakfast_menu,
        "lunch_dinner": lunch_dinner_menu,
        "all_selected_foods": breakfast_menu + lunch_dinner_menu,
        "nutrient_totals": final_totals
    }

    return decoded_menu


def print_decoded_menu(decoded_menu, dataset):
    print("\nBreakfast Menu:")
    for food_id in decoded_menu["breakfast"]:
        food = get_food_by_id(dataset, food_id)
        print(f"{food_id} - {food['name']}")

    print("\nLunch/Dinner Menu:")
    for food_id in decoded_menu["lunch_dinner"]:
        food = get_food_by_id(dataset, food_id)
        print(f"{food_id} - {food['name']}")

    print("\nNutrient Totals:")
    for nutrient, value in decoded_menu["nutrient_totals"].items():
        print(f"{nutrient}: {value:.2f}")


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

    print_decoded_menu(decoded_menu, dataset)