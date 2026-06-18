import random
import math
import json
from copy import deepcopy

from genetic_algorithms.chromosome import create_initial_population
from genetic_algorithms.decoder import decode_chromosome
from data.dri_loader import load_dri_for_user
from genetic_algorithms.fitness import calculate_objectives
from genetic_algorithms.crossover import order_crossover
from genetic_algorithms.mutation import swap_mutation
from genetic_algorithms.diversity import calculate_diversity_penalty


def dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def build_objectives(fitness, objective_names):
    penalty = float(fitness.get("total_penalty", fitness["penalty"]))

    result = []

    for obj in objective_names:
        if obj == "preference":
            result.append(-float(fitness["preference"]) + penalty)

        elif obj == "cost":
            result.append(float(fitness["cost"]) + penalty)

        elif obj == "time":
            result.append(float(fitness["time"]) + penalty)

        elif obj == "co2":
            result.append(float(fitness["co2"]) + penalty)

    return result


def evaluate_one(
    chromosome,
    dataset,
    dri_df,
    user_id,
    objective_names,
    use_diversity=True,
    penalty_weight=1.0,
    diversity_alpha=0.5
):
    decoded = decode_chromosome(chromosome, dataset, dri_df)
    fitness = calculate_objectives(decoded, dataset, dri_df, user_id, penalty_weight)

    selected_ids = decoded["all_selected_foods"]
    selected_df = dataset[dataset["id"].isin(selected_ids)].copy()

    if use_diversity:
        div_penalty, div_count = calculate_diversity_penalty(
            selected_df,
            alpha=diversity_alpha
        )
    else:
        div_penalty = 0.0
        div_count = int(selected_df["foodGroupId"].nunique())

    total_penalty = float(fitness["penalty"]) + float(div_penalty)
    penalized_pref = float(fitness["preference"]) - penalty_weight * total_penalty

    fitness["diversity_penalty"] = div_penalty
    fitness["total_penalty"] = total_penalty
    fitness["penalized_preference"] = penalized_pref
    fitness["diversity"] = div_count

    return {
        "chromosome": chromosome,
        "decoded_menu": decoded,
        "fitness": fitness,
        "objectives": build_objectives(fitness, objective_names),
        "selected_food_ids": selected_ids,
        "spea2_strength": 0.0,
        "spea2_raw_fitness": 0.0,
        "spea2_density": 0.0,
        "spea2_fitness": 0.0
    }


def evaluate_all(
    population,
    dataset,
    dri_df,
    user_id,
    objective_names,
    use_diversity,
    penalty_weight,
    diversity_alpha
):
    sonuclar = []

    for ch in population:
        sonuclar.append(
            evaluate_one(
                ch,
                dataset,
                dri_df,
                user_id,
                objective_names,
                use_diversity,
                penalty_weight,
                diversity_alpha
            )
        )

    return sonuclar


def spea2_raw_hesapla(objectives):
    n = len(objectives)
    strengths = [0.0] * n
    raw = [0.0] * n

    for i in range(n):
        for j in range(n):
            if i != j and dominates(objectives[i], objectives[j]):
                strengths[i] += 1

    for i in range(n):
        for j in range(n):
            if i != j and dominates(objectives[j], objectives[i]):
                raw[i] += strengths[j]

    return strengths, raw


def normalize(objectives):
    if not objectives:
        return []

    m = len(objectives[0])
    mins = [min(o[k] for o in objectives) for k in range(m)]
    maxs = [max(o[k] for o in objectives) for k in range(m)]

    result = []

    for o in objectives:
        row = []

        for k in range(m):
            d = maxs[k] - mins[k]
            row.append(0.0 if d == 0 else (o[k] - mins[k]) / d)

        result.append(row)

    return result


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def calc_density(objectives):
    n = len(objectives)

    if n <= 1:
        return [0.0] * n

    norm = normalize(objectives)
    k = max(1, int(math.sqrt(n)))
    densities = []

    for i in range(n):
        dists = sorted(
            euclidean(norm[i], norm[j])
            for j in range(n)
            if i != j
        )
        kth = dists[min(k - 1, len(dists) - 1)]
        densities.append(1.0 / (kth + 2.0))

    return densities


def assign_fitness(evaluations):
    objectives = [ev["objectives"] for ev in evaluations]
    strengths, raw = spea2_raw_hesapla(objectives)
    density = calc_density(objectives)

    result = []

    for i, ev in enumerate(evaluations):
        updated = ev.copy()
        updated["spea2_strength"] = strengths[i]
        updated["spea2_raw_fitness"] = raw[i]
        updated["spea2_density"] = density[i]
        updated["spea2_fitness"] = raw[i] + density[i]
        result.append(updated)

    return result


def truncate_archive(selected, evaluations, archive_size):
    selected = selected[:]

    while len(selected) > archive_size:
        objectives = [evaluations[i]["objectives"] for i in selected]
        norm = normalize(objectives)

        min_dist = float("inf")
        remove_idx = 0

        for i in range(len(norm)):
            dists = sorted(
                euclidean(norm[i], norm[j])
                for j in range(len(norm))
                if i != j
            )

            if dists and dists[0] < min_dist:
                min_dist = dists[0]
                remove_idx = i

        selected.pop(remove_idx)

    return selected


def environmental_selection(evaluations, archive_size):
    evaluated = assign_fitness(evaluations)

    selected = [
        i
        for i, ev in enumerate(evaluated)
        if ev["spea2_raw_fitness"] == 0.0
    ]

    if len(selected) < archive_size:
        remaining = [
            i
            for i in range(len(evaluated))
            if i not in selected
        ]
        remaining.sort(key=lambda i: evaluated[i]["spea2_fitness"])
        selected += remaining[:archive_size - len(selected)]

    elif len(selected) > archive_size:
        selected = truncate_archive(selected, evaluated, archive_size)

    archive = [deepcopy(evaluated[i]["chromosome"]) for i in selected]
    archive_evals = [evaluated[i] for i in selected]

    return archive, archive_evals


def tournament_select(archive, archive_evals):
    if len(archive) == 1:
        return deepcopy(archive[0])

    i, j = random.sample(range(len(archive)), 2)

    if archive_evals[i]["spea2_fitness"] <= archive_evals[j]["spea2_fitness"]:
        return deepcopy(archive[i])

    return deepcopy(archive[j])


def create_offspring(archive, archive_evals, population_size, pc=0.9):
    offspring = []

    while len(offspring) < population_size:
        p1 = tournament_select(archive, archive_evals)
        p2 = tournament_select(archive, archive_evals)

        c1, c2 = order_crossover(p1, p2, pc=pc)

        offspring.append(swap_mutation(c1))

        if len(offspring) < population_size:
            offspring.append(swap_mutation(c2))

    return offspring


def run_spea2(
    dataset,
    user_id,
    population_size=50,
    archive_size=50,
    generations=50,
    objective_names=None,
    use_diversity=True,
    penalty_weight=1.0,
    diversity_alpha=0.5,
    pc=0.9,
    random_seed=None
):
    if random_seed is not None:
        random.seed(random_seed)

    if objective_names is None:
        objective_names = ["preference", "cost", "time"]

    dri_df = load_dri_for_user(user_id)
    population = create_initial_population(dataset, population_size)

    archive = []
    archive_evals = []
    history = []

    for gen in range(generations):
        combined = population + archive

        evaluations = evaluate_all(
            combined,
            dataset,
            dri_df,
            user_id,
            objective_names,
            use_diversity,
            penalty_weight,
            diversity_alpha
        )

        archive, archive_evals = environmental_selection(
            evaluations,
            archive_size
        )

        best_pref = max(
            ev["fitness"]["preference"]
            for ev in archive_evals
        )

        avg_penalty = sum(
            ev["fitness"]["total_penalty"]
            for ev in archive_evals
        ) / len(archive_evals)

        avg_div = sum(
            ev["fitness"]["diversity"]
            for ev in archive_evals
        ) / len(archive_evals)

        non_dominated = [
            ev
            for ev in archive_evals
            if ev["spea2_raw_fitness"] == 0
        ]

        history.append({
            "generation": gen,
            "archive_size": len(archive),
            "non_dominated_size": len(non_dominated),
            "best_preference": best_pref,
            "average_penalty": avg_penalty,
            "average_diversity": avg_div,
            "front_objectives": json.dumps(
                [
                    ev["objectives"]
                    for ev in non_dominated
                ]
            )
        })

        print(
            f"Gen {gen + 1}/{generations} | "
            f"Archive: {len(archive)} | "
            f"Best pref: {best_pref:.4f} | "
            f"Avg penalty: {avg_penalty:.6f} | "
            f"Avg div: {avg_div:.2f}"
        )

        population = create_offspring(
            archive,
            archive_evals,
            population_size,
            pc
        )

    pareto = [
        ev
        for ev in archive_evals
        if ev["spea2_raw_fitness"] == 0
    ]

    return {
        "algorithm": "spea2",
        "user_id": user_id,
        "objective_names": objective_names,
        "use_diversity": use_diversity,
        "archive": archive,
        "archive_evaluations": archive_evals,
        "pareto_front": pareto,
        "history": history
    }


def print_spea2_summary(result):
    evals = result["archive_evaluations"]

    best_pref = max(
        evals,
        key=lambda ev: ev["fitness"]["preference"]
    )

    lowest_penalty = min(
        evals,
        key=lambda ev: ev["fitness"]["total_penalty"]
    )

    max_pref = max(
        ev["fitness"]["preference"]
        for ev in evals
    )

    max_pen = max(
        ev["fitness"]["total_penalty"]
        for ev in evals
    )

    balanced = min(
        evals,
        key=lambda ev:
            -ev["fitness"]["preference"] / (max_pref + 1e-9)
            + ev["fitness"]["total_penalty"] / (max_pen + 1e-9)
    )

    print("\nSPEA2 Summary")
    print("User:", result["user_id"])
    print("Archive size:", len(evals))

    for label, ev in [
        ("Best preference", best_pref),
        ("Lowest penalty", lowest_penalty),
        ("Balanced", balanced)
    ]:
        f = ev["fitness"]

        print(
            f"{label} | "
            f"Pref: {f['preference']:.2f} | "
            f"Cost: {f['cost']:.2f} | "
            f"Time: {f['time']:.2f} | "
            f"Penalty: {f['total_penalty']:.4f} | "
            f"Div: {f['diversity']} | "
            f"SPEA2: {ev['spea2_fitness']:.4f}"
        )


if __name__ == "__main__":
    from data_loader import load_dataset

    dataset = load_dataset()

    result = run_spea2(
        dataset=dataset,
        user_id=1,
        population_size=100,
        archive_size=20,
        generations=50,
        objective_names=["preference", "cost", "time"],
        use_diversity=True,
        penalty_weight=1.0,
        diversity_alpha=0.5,
        pc=0.9,
        random_seed=42
    )

    print_spea2_summary(result)