# Multi-Objective Diet Optimization Problem (MODP)

This project solves a multi-objective daily diet/menu optimization problem using evolutionary multi-objective optimization algorithms.

The goal is to recommend a daily menu consisting of breakfast and lunch+dinner foods selected from the provided MySQL database.

## Implemented Algorithms

The following algorithms are implemented from scratch:

- NSGA-II
- SPEA2

The `pymoo` library is used only for hypervolume calculation during evaluation/visualization.

Chromosome representation, decoding, crossover, mutation, penalty calculation, diversity mechanism, NSGA-II, and SPEA2 logic are implemented in our own code.

## Selected Objectives

The project handout requires exactly 3 objectives.

We selected:

- Maximize user preference
- Minimize cost
- Minimize preparation + cooking time

CO2 is also calculated and reported, but it is not one of the optimized objectives in the final experiments.

## Diversity Mechanism

Diversity is implemented as a soft penalty term:

```text
R_total = R + alpha * (1 / distinct_food_group_count)
```

This encourages menus with more distinct food groups.

The experiments are run both with and without the diversity mechanism.

## Project Structure

```text
heuristic-proje/
    data_loader.py
    dri_loader.py
    user_preference_loader.py
    chromosome.py
    decoder.py
    penalty.py
    fitness.py
    diversity.py
    crossover.py
    mutation.py
    nsga2.py
    spea2.py
    experiment_runner.py
    visualization.py
    README.md

results/
    pareto_all.csv
    history_all.csv
    history_all_hv.csv
    sample_menus.csv
    sample_nutrient_summary.csv
    hypervolume_reference_point.csv
    summary_hypervolume.csv

plots/
    pareto_nsga2.png
    pareto_spea2.png
    algorithm_comparison_overlay.png
    user_comparison.png
    hypervolume_convergence.png
    diversity_impact_nsga2.png
    diversity_impact_spea2.png
```

## Requirements

Install the required Python packages:

```bash
pip install pandas numpy matplotlib pymoo mysql-connector-python
```

If you are using Anaconda, the same packages can be installed with:

```bash
conda install pandas numpy matplotlib
pip install pymoo mysql-connector-python
```

## Database Setup

The project reads data directly from the provided MySQL database.

Default database settings are defined in:

- `data_loader.py`
- `dri_loader.py`
- `user_preference_loader.py`

Default connection configuration:

```python
host="localhost"
user="root"
password=""
database="modp"
port=3306
```

Before running the project, make sure:

1. MySQL server is running.
2. The provided database is imported.
3. The database name is `modp`.
4. The database credentials in the loader files match your local MySQL setup.

## How to Run

Run all experiments:

```bash
python experiment_runner.py
```

This generates the main CSV result files inside the `results/` folder.

Then generate plots and hypervolume outputs:

```bash
python visualization.py
```

This generates the plots inside the `plots/` folder and hypervolume-related CSV files inside `results/`.

## Experiment Settings

The main experiment settings are defined in `experiment_runner.py`:

```python
USERS = [1, 97]
ALGORITHMS = ["nsga2", "spea2"]
DIVERSITY_SETTINGS = [("div_on", True), ("div_off", False)]

POPULATION_SIZE = 20
GENERATIONS = 50
ARCHIVE_SIZE = 20

OBJECTIVES = ("cost", "time")
OBJECTIVE_NAMES = ["preference", "cost", "time"]

PENALTY_WEIGHT = 1.0
DIVERSITY_ALPHA = 0.5
PC = 0.9
SEED = 42
```

User 1 corresponds to the non-vegetarian user.

User 97 corresponds to the vegetarian user in the provided database.

## Generated Results

The experiment runner generates:

```text
results/pareto_all.csv
results/history_all.csv
results/sample_menus.csv
results/sample_nutrient_summary.csv
```

The visualization script generates:

```text
results/history_all_hv.csv
results/hypervolume_reference_point.csv
results/summary_hypervolume.csv
```

and the following plots:

```text
plots/pareto_nsga2.png
plots/pareto_spea2.png
plots/algorithm_comparison_overlay.png
plots/user_comparison.png
plots/hypervolume_convergence.png
plots/diversity_impact_nsga2.png
plots/diversity_impact_spea2.png
```

## Output Explanation

### `pareto_all.csv`

Contains Pareto front solutions for each experiment combination:

```text
algorithm × user × diversity setting
```

### `history_all.csv`

Contains generation-level optimization history and Pareto front objective values.

### `history_all_hv.csv`

Contains the same history data with hypervolume values added.

### `sample_menus.csv`

Contains selected food items for representative Pareto solutions.

### `sample_nutrient_summary.csv`

Contains nutrient totals, DRI lower/upper bounds, nutrient status, and constraint compliance count for representative Pareto solutions.

### `hypervolume_reference_point.csv`

Contains the fixed reference point used for hypervolume calculation.

The reference point is computed as the worst observed objective value across all runs plus 10% margin.

### `summary_hypervolume.csv`

Contains max, last, and mean hypervolume values for each algorithm/user/diversity experiment.

## Notes

- NSGA-II and SPEA2 are implemented from scratch.
- `pymoo` is only used for hypervolume calculation.
- The chromosome representation uses two independent permutations:
  - breakfast foods
  - lunch+dinner foods
- Decoding is greedy and follows the DRI-based constraints described in the project handout.
- Penalty is calculated using nutrient violations.
- Diversity is implemented as a soft penalty and is compared with the no-diversity setting.
