from data.data_loader import load_dataset
from data.dri_loader import load_dri_for_user
from genetic_algorithms.chromosome import create_random_chromosome
from genetic_algorithms.decoder import decode_chromosome


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


def calculate_penalty(nutrient_totals, dri_df):
    dri_dict = convert_dri_to_dict(dri_df)

    total_low_violation = 0.0
    total_high_violation = 0.0
    violation_details = {}

    for nutrient in NUTRIENT_COLUMNS:
        value = float(nutrient_totals[nutrient])
        rll = dri_dict[nutrient]["RLL"]
        rul = dri_dict[nutrient]["RUL"]

        denominator = rul - rll

        if denominator <= 0:
            low_violation = 0.0
            high_violation = 0.0
        else:
            low_violation = max(0.0, rll - value) / denominator
            high_violation = max(0.0, value - rul) / denominator

        total_low_violation += low_violation
        total_high_violation += high_violation

        violation_details[nutrient] = {
            "value": value,
            "RLL": rll,
            "RUL": rul,
            "low_violation": low_violation,
            "high_violation": high_violation
        }

    penalty = (0.7 * total_low_violation) + (0.3 * total_high_violation)

    return penalty, violation_details


def print_penalty_report(penalty, violation_details):
    print("\nPenalty Report:")

    for nutrient, data in violation_details.items():
        print(
            f"{nutrient}: "
            f"value={data['value']:.2f}, "
            f"RLL={data['RLL']:.2f}, "
            f"RUL={data['RUL']:.2f}, "
            f"low_violation={data['low_violation']:.4f}, "
            f"high_violation={data['high_violation']:.4f}"
        )

    print(f"\nTotal penalty: {penalty:.6f}")


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

    penalty, violation_details = calculate_penalty(
        nutrient_totals=decoded_menu["nutrient_totals"],
        dri_df=user_dri
    )

    print_penalty_report(penalty, violation_details)