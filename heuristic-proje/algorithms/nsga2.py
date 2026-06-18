import random
import math
import json
from copy import deepcopy

from genetic_algorithms.chromosome import create_initial_population
from genetic_algorithms.decoder import decode_chromosome
from genetic_algorithms.fitness import calculate_objectives
from genetic_algorithms.crossover import order_crossover
from genetic_algorithms.mutation import swap_mutation
from genetic_algorithms.diversity import calculate_diversity_penalty

def make_objective_vector(fitness, penalty_weight=1.0, objectives=("cost", "time")):
    penalty = fitness["penalty"]
    vector = [-fitness["preference"] + penalty_weight * penalty]
    if "cost" in objectives:
        vector.append(fitness["cost"] + penalty_weight * penalty)
    if "time" in objectives:
        vector.append(fitness["time"] + penalty_weight * penalty)
    if "co2" in objectives:
        vector.append(fitness["co2"] + penalty_weight * penalty)
    return vector

def dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))

def fast_non_dominated_sort(objective_vectors):
    n = len(objective_vectors)
    domination_sets = [[] for _ in range(n)]
    dominated_counts = [0] * n
    ranks = [0] * n
    fronts = [[]]
    for p in range(n):
        for q in range(n):
            if p == q:
                continue

            if dominates(objective_vectors[p], objective_vectors[q]):
                domination_sets[p].append(q)

            elif dominates(objective_vectors[q], objective_vectors[p]):
                dominated_counts[p] += 1

        if dominated_counts[p] == 0:
            ranks[p] = 0
            fronts[0].append(p)
    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in domination_sets[p]:
                dominated_counts[q] -= 1

                if dominated_counts[q] == 0:
                    ranks[q] = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    fronts.pop()

    return fronts, ranks

def calculate_crowding_distance(front, objective_vectors):
    distance = {idx: 0.0 for idx in front}

    if len(front) <= 2:
        for idx in front:
            distance[idx] = math.inf
        return distance

    num_objectives = len(objective_vectors[0])

    for obj_idx in range(num_objectives):
        sorted_front = sorted(
            front,
            key=lambda idx: objective_vectors[idx][obj_idx]
        )
        distance[sorted_front[0]] = math.inf
        distance[sorted_front[-1]] = math.inf

        min_value = objective_vectors[sorted_front[0]][obj_idx]
        max_value = objective_vectors[sorted_front[-1]][obj_idx]

        if max_value == min_value:
            continue

        for i in range(1, len(sorted_front) - 1):
            previous_value = objective_vectors[sorted_front[i - 1]][obj_idx]
            next_value = objective_vectors[sorted_front[i + 1]][obj_idx]

            distance[sorted_front[i]] += (
                next_value - previous_value
            ) / (max_value - min_value)

    return distance

def assign_rank_and_crowding(individuals):
    objective_vectors = [ind["objectives"] for ind in individuals]
    fronts, ranks = fast_non_dominated_sort(objective_vectors)
    for i, ind in enumerate(individuals):
        ind["rank"] = ranks[i]
        ind["crowding_distance"] = 0.0

    for front in fronts:
        distances = calculate_crowding_distance(front, objective_vectors)

        for idx in front:
            individuals[idx]["crowding_distance"] = distances[idx]
    return fronts

def evaluate_population(
    population,
    dataset,
    dri_df,
    user_id,
    penalty_weight,
    objectives,
    use_diversity=True,
    diversity_alpha=0.5
):
    evaluated = []
    for chromosome in population:
        decoded_menu = decode_chromosome(
            chromosome=chromosome,
            dataset=dataset,
            dri_df=dri_df
        )
        fitness = calculate_objectives(
            decoded_menu=decoded_menu,
            dataset=dataset,
            dri_df=dri_df,
            user_id=user_id,
            penalty_weight=penalty_weight
        )
        selected_ids = decoded_menu["all_selected_foods"]
        selected_df = dataset[dataset["id"].isin(selected_ids)].copy()
        if use_diversity:
            diversity_penalty, diversity_count = calculate_diversity_penalty(
                selected_df,
                alpha=diversity_alpha
            )
        else:
            diversity_penalty = 0.0
            diversity_count = int(selected_df["foodGroupId"].nunique())

        nutrient_penalty = float(fitness["penalty"])
        total_penalty = nutrient_penalty + float(diversity_penalty)
        penalized_preference = float(fitness["preference"]) - penalty_weight * total_penalty

        fitness["nutrient_penalty"] = nutrient_penalty
        fitness["diversity_penalty"] = float(diversity_penalty)
        fitness["total_penalty"] = total_penalty
        fitness["penalty"] = total_penalty
        fitness["penalized_preference"] = penalized_preference
        fitness["diversity"] = diversity_count

        objective_vector = make_objective_vector(
            fitness=fitness,
            penalty_weight=penalty_weight,
            objectives=objectives
        )
        evaluated.append({
            "chromosome": chromosome,
            "decoded_menu": decoded_menu,
            "fitness": fitness,
            "objectives": objective_vector,
            "rank": None,
            "crowding_distance": 0.0
        })
    assign_rank_and_crowding(evaluated)

    return evaluated

def tournament_selection(evaluated_population):
    a, b = random.sample(evaluated_population, 2)

    if a["rank"] < b["rank"]:
        return deepcopy(a["chromosome"])
    if b["rank"] < a["rank"]:
        return deepcopy(b["chromosome"])
    if a["crowding_distance"] > b["crowding_distance"]:
        return deepcopy(a["chromosome"])
    return deepcopy(b["chromosome"])

def create_offspring(evaluated_population, population_size, pc=0.9):
    offspring = []
    while len(offspring) < population_size:
        parent1 = tournament_selection(evaluated_population)
        parent2 = tournament_selection(evaluated_population)
        child1, child2 = order_crossover(parent1, parent2, pc=pc)
        child1 = swap_mutation(child1)
        child2 = swap_mutation(child2)
        offspring.append(child1)

        if len(offspring) < population_size:
            offspring.append(child2)

    return offspring
def environmental_selection(combined_population, population_size):
    assign_rank_and_crowding(combined_population)
    fronts = {}
    for ind in combined_population:
        fronts.setdefault(ind["rank"], []).append(ind)
    next_population = []
    for rank in sorted(fronts.keys()):
        front = fronts[rank]

        if len(next_population) + len(front) <= population_size:
            next_population.extend(front)
        else:
            remaining_slots = population_size - len(next_population)
            sorted_front = sorted(
                front,
                key=lambda ind: ind["crowding_distance"],
                reverse=True
            )
            next_population.extend(sorted_front[:remaining_slots])
            break
    assign_rank_and_crowding(next_population)
    return next_population
def run_nsga2(
    dataset,
    dri_df,
    user_id,
    population_size=100,
    generations=50,
    objectives=("cost", "time"),
    penalty_weight=1.0,
    use_diversity=True,
    diversity_alpha=0.5,
    pc=0.9,
    seed=42
):
    if seed is not None:
        random.seed(seed)
    if len(objectives) != 2:
        raise ValueError("Handout'a göre preference + seçilen 2 objective olmalı.")
    population = create_initial_population(
        dataset=dataset,
        population_size=population_size
    )
    evaluated_population = evaluate_population(
        population=population,
        dataset=dataset,
        dri_df=dri_df,
        user_id=user_id,
        penalty_weight=penalty_weight,
        objectives=objectives,
        use_diversity=use_diversity,
        diversity_alpha=diversity_alpha
    )
    history = []
    for generation in range(generations):
        offspring_population = create_offspring(
            evaluated_population=evaluated_population,
            population_size=population_size,
            pc=pc
        )
        evaluated_offspring = evaluate_population(
            population=offspring_population,
            dataset=dataset,
            dri_df=dri_df,
            user_id=user_id,
            penalty_weight=penalty_weight,
            objectives=objectives,
            use_diversity=use_diversity,
            diversity_alpha=diversity_alpha
        )
        combined_population = evaluated_population + evaluated_offspring
        evaluated_population = environmental_selection(
            combined_population=combined_population,
            population_size=population_size
        )
        first_front = [
            ind for ind in evaluated_population
            if ind["rank"] == 0
        ]
        avg_penalty = sum(
            ind["fitness"]["penalty"]
            for ind in evaluated_population
        ) / len(evaluated_population)
        avg_nutrient_penalty = sum(
            ind["fitness"].get("nutrient_penalty", ind["fitness"]["penalty"])
            for ind in evaluated_population
        ) / len(evaluated_population)
        avg_diversity_penalty = sum(
            ind["fitness"].get("diversity_penalty", 0.0)
            for ind in evaluated_population
        ) / len(evaluated_population)
        avg_diversity = sum(
            ind["fitness"]["diversity"]
            for ind in evaluated_population
        ) / len(evaluated_population)
        history.append({
            "generation": generation,
            "first_front_size": len(first_front),
            "best_preference": max(
                ind["fitness"]["preference"]
                for ind in evaluated_population
            ),
            "min_cost": min(
                ind["fitness"]["cost"]
                for ind in evaluated_population
            ),
            "min_time": min(
                ind["fitness"]["time"]
                for ind in evaluated_population
            ),
            "min_co2": min(
                ind["fitness"]["co2"]
                for ind in evaluated_population
            ),
            "avg_penalty": avg_penalty,
            "avg_nutrient_penalty": avg_nutrient_penalty,
            "avg_diversity_penalty": avg_diversity_penalty,
            "avg_diversity": avg_diversity,
            "front_objectives": json.dumps(
                [ind["objectives"] for ind in first_front]
            )
        })
        print(
            f"Generation {generation + 1}/{generations} | "
            f"Front0={len(first_front)} | "
            f"AvgPenalty={avg_penalty:.4f} | "
            f"AvgDiv={avg_diversity:.2f}"
        )
    pareto_front = [
        ind for ind in evaluated_population
        if ind["rank"] == 0
    ]
    return {
        "algorithm": "nsga2",
        "user_id": user_id,
        "population": evaluated_population,
        "archive": pareto_front,
        "archive_evaluations": pareto_front,
        "pareto_front": pareto_front,
        "history": history,
        "objectives": ("preference",) + tuple(objectives),
        "use_diversity": use_diversity,
        "diversity_alpha": diversity_alpha
    }
def print_nsga2_summary(result):
    pareto_front = result["pareto_front"]
    if not pareto_front:
        print("\nNSGA2 Summary")
        print("Pareto front is empty.")
        return
    best_preference = max(
        pareto_front,
        key=lambda ind: ind["fitness"]["preference"]
    )
    lowest_penalty = min(
        pareto_front,
        key=lambda ind: ind["fitness"]["penalty"]
    )
    balanced = min(
        pareto_front,
        key=lambda ind: ind["fitness"]["penalty"] - 0.01 * ind["fitness"]["preference"]
    )
    print("\nNSGA2 Summary")
    print("User:", result["user_id"])
    print("Pareto size:", len(pareto_front))
    print("Diversity enabled:", result["use_diversity"])

    for label, ind in [
        ("Best preference", best_preference),
        ("Lowest penalty", lowest_penalty),
        ("Balanced", balanced)
    ]:
        f = ind["fitness"]

        print(
            f"{label} | "
            f"Pref: {f['preference']:.2f} | "
            f"Cost: {f['cost']:.2f} | "
            f"Time: {f['time']:.2f} | "
            f"CO2: {f['co2']:.2f} | "
            f"Penalty: {f['penalty']:.4f} | "
            f"Nutrient Penalty: {f.get('nutrient_penalty', f['penalty']):.4f} | "
            f"Diversity Penalty: {f.get('diversity_penalty', 0.0):.4f} | "
            f"Div: {f['diversity']}"
        )

if __name__ == "__main__":
    from data_loader import load_dataset
    from dri_loader import load_dri_for_user

    dataset = load_dataset()
    user_id = 1
    dri_df = load_dri_for_user(user_id=user_id)
    result = run_nsga2(
        dataset=dataset,
        dri_df=dri_df,
        user_id=user_id,
        population_size=100,
        generations=50,
        objectives=("cost", "time"),
        penalty_weight=1.0,
        use_diversity=True,
        diversity_alpha=0.5,
        pc=0.9,
        seed=42
    )
    print_nsga2_summary(result)