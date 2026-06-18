import mysql.connector
import pandas as pd


TARGET_NUTRIENTS = {
    "fiber": 4,
    "energy": 5,
    "carbohydrate": 8,
    "protein": 15,
    "sodium": 17
}


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="modp",
        port=3306
    )


def load_foods():
    conn = get_connection()

    query = """
    SELECT 
        id,
        name,
        foodGroupId,
        cost,
        preparingTime,
        cookingTime,
        co2
    FROM foods
    ORDER BY id;
    """

    foods = pd.read_sql(query, conn)
    conn.close()
    return foods


def load_food_nutrients():
    conn = get_connection()

    query = """
    SELECT 
        foodId,
        nutrientId,
        quantity
    FROM food_nutrients;
    """

    food_nutrients = pd.read_sql(query, conn)
    conn.close()
    return food_nutrients


def build_nutrient_matrix(food_nutrients):
    selected_ids = list(TARGET_NUTRIENTS.values())

    filtered = food_nutrients[
        food_nutrients["nutrientId"].isin(selected_ids)
    ].copy()

    reverse_map = {
        nutrient_id: name
        for name, nutrient_id in TARGET_NUTRIENTS.items()
    }

    filtered["nutrient_name"] = filtered["nutrientId"].map(reverse_map)

    nutrient_matrix = filtered.pivot_table(
        index="foodId",
        columns="nutrient_name",
        values="quantity",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    return nutrient_matrix


def load_dataset():
    foods = load_foods()
    food_nutrients = load_food_nutrients()

    nutrient_matrix = build_nutrient_matrix(food_nutrients)

    dataset = foods.merge(
        nutrient_matrix,
        left_on="id",
        right_on="foodId",
        how="left"
    )

    dataset = dataset.fillna(0)

    dataset["totalTime"] = dataset["preparingTime"] + dataset["cookingTime"]

    return dataset


if __name__ == "__main__":
    dataset = load_dataset()

    print("Dataset shape:", dataset.shape)
    print(dataset.head())

    print("\nSelected columns:")
    print(dataset[
        [
            "id",
            "name",
            "foodGroupId",
            "cost",
            "totalTime",
            "co2",
            "energy",
            "protein",
            "carbohydrate",
            "fiber",
            "sodium"
        ]
    ].head())

