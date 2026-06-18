import mysql.connector
import pandas as pd


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
        preference,
        preference2,
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

    nutrients = pd.read_sql(query, conn)
    conn.close()
    return nutrients


def load_dri():
    conn = get_connection()

    query = """
    SELECT 
        id,
        nutrient_id,
        low_age,
        up_age,
        gender,
        RLL,
        RUL
    FROM dri;
    """

    dri = pd.read_sql(query, conn)
    conn.close()
    return dri


if __name__ == "__main__":
    foods = load_foods()
    food_nutrients = load_food_nutrients()
    dri = load_dri()

    print("Foods shape:", foods.shape)
    print(foods.head())

    print("\nFood nutrients shape:", food_nutrients.shape)
    print(food_nutrients.head())

    print("\nDRI shape:", dri.shape)
    print(dri.head())