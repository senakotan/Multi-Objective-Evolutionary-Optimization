from data_loader import load_dataset
from dri_loader import load_dri_for_user
from chromosome import create_random_chromosome
from decoder import decode_chromosome


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


def check_constraints(nutrient_totals, dri_df):
    dri_dict = convert_dri_to_dict(dri_df)

    results = {}

    for nutrient in NUTRIENT_COLUMNS:
        value = nutrient_totals[nutrient]
        rll = dri_dict[nutrient]["RLL"]
        rul = dri_dict[nutrient]["RUL"]

        if value < rll:
            status = "LOW"
        elif value > rul:
            status = "HIGH"
        else:
            status = "OK"

        results[nutrient] = {
            "value": value,
            "RLL": rll,
            "RUL": rul,
            "status": status
        }

    return results


def print_constraint_report(results):
    print("\nConstraint Report:")

    for nutrient, data in results.items():
        print(
            f"{nutrient}: "
            f"value={data['value']:.2f}, "
            f"RLL={data['RLL']:.2f}, "
            f"RUL={data['RUL']:.2f}, "
            f"status={data['status']}"
        )


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

    results = check_constraints(
        nutrient_totals=decoded_menu["nutrient_totals"],
        dri_df=user_dri
    )

    print_constraint_report(results)