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
genetic_algorithms/
algorithms/
experiments/
visualization/
results/
plots/
```

## Technologies

- Python
- Pandas
- NumPy
- MySQL

