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


def load_user_info(user_id):
    conn = get_connection()

    query = f"""
    SELECT 
        id,
        age,
        gender
    FROM `user`
    WHERE id = {user_id};
    """

    user_info = pd.read_sql(query, conn)
    conn.close()

    if user_info.empty:
        raise ValueError(f"User with id {user_id} was not found.")

    age = int(user_info.iloc[0]["age"])
    gender = str(user_info.iloc[0]["gender"]).lower()

    return age, gender


def load_dri_for_user(user_id):
    age, gender = load_user_info(user_id)

    conn = get_connection()

    nutrient_ids = tuple(TARGET_NUTRIENTS.values())

    query = f"""
    SELECT 
        nutrient_id,
        RLL,
        RUL
    FROM dri
    WHERE nutrient_id IN {nutrient_ids}
      AND low_age <= {age}
      AND up_age >= {age}
      AND LOWER(gender) = '{gender}';
    """

    dri = pd.read_sql(query, conn)
    conn.close()

    reverse_map = {
        nutrient_id: name
        for name, nutrient_id in TARGET_NUTRIENTS.items()
    }

    dri["nutrient_name"] = dri["nutrient_id"].map(reverse_map)

    return dri

if __name__ == "__main__":
    user1_id = 1
    user2_id = 97

    user1_dri = load_dri_for_user(user1_id)
    user2_dri = load_dri_for_user(user2_id)

    print("User 1 DRI:")
    print(user1_dri)

    print("\nUser 2 DRI:")
    print(user2_dri)