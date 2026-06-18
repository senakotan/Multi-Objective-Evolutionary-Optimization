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


def load_user_preferences(user_id):
    conn = get_connection()

    query = f"""
    SELECT 
        userId,
        foodId,
        preference
    FROM user_foods
    WHERE userId = {user_id}
      AND preference IS NOT NULL;
    """

    user_preferences = pd.read_sql(query, conn)
    conn.close()

    preference_dict = {}

    for _, row in user_preferences.iterrows():
        food_id = int(row["foodId"])
        preference = float(row["preference"])
        preference_dict[food_id] = preference

    return preference_dict


if __name__ == "__main__":
    for user_id in [1, 97]:
        preference_dict = load_user_preferences(user_id)

        print("User ID:", user_id)
        print("Preference count:", len(preference_dict))

        print("\nFirst 10 preferences:")
        for i, (food_id, preference) in enumerate(preference_dict.items()):
            if i == 10:
                break
            print(food_id, preference)

        print("-" * 40)