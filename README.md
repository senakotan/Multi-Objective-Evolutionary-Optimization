# Multi-Objective Evolutionary Optimization

This project implements a multi-objective optimization framework using evolutionary algorithms to generate optimal menu solutions under multiple constraints.

The system evaluates candidate solutions according to nutritional requirements, user preferences, cost, preparation time, carbon footprint, and diversity, producing Pareto-optimal solutions using NSGA-II and SPEA2.

## Algorithms

- NSGA-II (Non-dominated Sorting Genetic Algorithm II)
- SPEA2 (Strength Pareto Evolutionary Algorithm 2)

## Features

- Two-part chromosome representation
  - Breakfast
  - Lunch/Dinner
- Multi-objective optimization
- Penalty-based constraint handling
- Diversity-aware optimization
- User-specific DRI constraints
- Pareto front generation and analysis

## Objectives

The optimization process considers:

- Preference Maximization
- Cost Minimization
- Preparation Time Minimization
- CO₂ Emission Minimization
- Nutritional Requirement Satisfaction
- Diversity Maximization

## Project Structure

```text
data/
├── data_loader.py
├── dri_loader.py
├── user_preference_loader.py
└── database_test.py

genetic_algorithms/
├── chromosome.py
├── decoder.py
├── fitness.py
├── penalty.py
├── constraint_checker.py
├── diversity.py
├── crossover.py
├── mutation.py
└── selection.py

algorithms/
├── nsga2.py
└── spea2.py

experiments/
└── experiment_runner.py

visualization/
└── visualization.py

results/
├── history_all.csv
├── history_all_hv.csv
├── pareto_all.csv
├── sample_menus.csv
├── sample_nutrient_summary.csv
└── summary_hypervolume.csv

plots/
├── pareto_nsga2.png
├── pareto_spea2.png
├── hypervolume_convergence.png
├── diversity_impact_nsga2.png
├── diversity_impact_spea2.png
├── user_comparison.png
└── algorithm_comparison_overlay.png


```

## Technologies

- Python
- Pandas
- NumPy
- MySQL

