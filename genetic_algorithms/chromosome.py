# Kahvaltı yiyeceklerini ayırmak
#Lunch/Dinner yiyeceklerini ayırmak
#Her iki kısmı ayrı ayrı karıştırmak
#Bir chromosome üretmek

import random
from data_loader import load_dataset


BREAKFAST_MIN_ID = 1
BREAKFAST_MAX_ID = 94

LUNCH_MIN_ID = 95
LUNCH_MAX_ID = 405


def get_breakfast_food_ids(dataset):
    breakfast_foods = dataset[
        (dataset["id"] >= BREAKFAST_MIN_ID) &
        (dataset["id"] <= BREAKFAST_MAX_ID)
    ]

    return breakfast_foods["id"].tolist()


def get_lunch_dinner_food_ids(dataset):
    lunch_dinner_foods = dataset[
        (dataset["id"] >= LUNCH_MIN_ID) &
        (dataset["id"] <= LUNCH_MAX_ID)
    ]

    return lunch_dinner_foods["id"].tolist()


def create_random_chromosome(dataset):
    breakfast_ids = get_breakfast_food_ids(dataset)
    lunch_dinner_ids = get_lunch_dinner_food_ids(dataset)

    random.shuffle(breakfast_ids)
    random.shuffle(lunch_dinner_ids)

    chromosome = {
        "breakfast": breakfast_ids,
        "lunch_dinner": lunch_dinner_ids
    }

    return chromosome


def create_initial_population(dataset, population_size):
    population = []

    for _ in range(population_size):
        chromosome = create_random_chromosome(dataset)
        population.append(chromosome)

    return population


if __name__ == "__main__":
    dataset = load_dataset()

    chromosome = create_random_chromosome(dataset)

    print("Breakfast gene count:", len(chromosome["breakfast"]))
    print("Lunch/Dinner gene count:", len(chromosome["lunch_dinner"]))

    print("\nFirst 10 breakfast genes:")
    print(chromosome["breakfast"][:10])

    print("\nFirst 10 lunch/dinner genes:")
    print(chromosome["lunch_dinner"][:10])

    population = create_initial_population(dataset, population_size=5)

    print("\nPopulation size:", len(population))