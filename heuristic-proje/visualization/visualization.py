import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pymoo.indicators.hv import HV


RESULTS_DIR = "results"
PLOTS_DIR = "plots"

PARETO_FILE = f"{RESULTS_DIR}/pareto_all.csv"
HISTORY_FILE = f"{RESULTS_DIR}/history_all.csv"

OBJECTIVE_X = "cost"
OBJECTIVE_Y = "preference"


def ensure_plots_dir():
    os.makedirs(PLOTS_DIR, exist_ok=True)


def parse_front_objectives(value):
    try:
        return json.loads(value)
    except Exception:
        return []


def compute_reference_point(history_df):
    points = []

    for value in history_df["front_objectives"]:
        points.extend(parse_front_objectives(value))

    if not points:
        raise ValueError("front_objectives boş. Önce experiment_runner.py çalıştır.")

    points = np.array(points, dtype=float)

    worst = points.max(axis=0)
    reference_point = worst + np.abs(worst) * 0.10

    pd.DataFrame({
        "objective_index": range(len(reference_point)),
        "reference_value": reference_point
    }).to_csv(f"{RESULTS_DIR}/hypervolume_reference_point.csv", index=False)

    return reference_point


def add_hypervolume(history_df, reference_point):
    hv = HV(ref_point=reference_point)
    values = []

    for value in history_df["front_objectives"]:
        front = parse_front_objectives(value)

        if not front:
            values.append(0.0)
        else:
            values.append(float(hv(np.array(front, dtype=float))))

    history_df["hypervolume"] = values
    history_df.to_csv(f"{RESULTS_DIR}/history_all_hv.csv", index=False)

    summary = history_df.groupby(
        ["algorithm", "user_id", "diversity_label"],
        as_index=False
    )["hypervolume"].agg(["max", "last", "mean"]).reset_index()

    summary.to_csv(f"{RESULTS_DIR}/summary_hypervolume.csv", index=False)

    return history_df


def plot_pareto_per_algorithm(pareto_df):
    for algorithm in pareto_df["algorithm"].unique():
        df = pareto_df[
            (pareto_df["algorithm"] == algorithm) &
            (pareto_df["diversity_label"] == "div_on")
        ]

        plt.figure()
        plt.scatter(df[OBJECTIVE_X], df[OBJECTIVE_Y], alpha=0.7)
        plt.xlabel(OBJECTIVE_X)
        plt.ylabel(OBJECTIVE_Y)
        plt.title(f"Pareto Front - {algorithm.upper()}")

        plt.grid(True)
        plt.savefig(f"{PLOTS_DIR}/pareto_{algorithm}.png", dpi=300, bbox_inches="tight")
        plt.close()


def plot_algorithm_overlay(pareto_df):
    df = pareto_df[
        (pareto_df["user_id"] == 1) &
        (pareto_df["diversity_label"] == "div_on")
    ]

    plt.figure()

    for algorithm in df["algorithm"].unique():
        part = df[df["algorithm"] == algorithm]
        plt.scatter(part[OBJECTIVE_X], part[OBJECTIVE_Y], alpha=0.7, label=algorithm.upper())

    plt.xlabel(OBJECTIVE_X)
    plt.ylabel(OBJECTIVE_Y)
    plt.title("Algorithm Comparison - Pareto Overlay")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/algorithm_comparison_overlay.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_user_comparison(pareto_df):
    algorithms = ["nsga2", "spea2"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for ax, algorithm in zip(axes, algorithms):
        df = pareto_df[
            (pareto_df["algorithm"] == algorithm) &
            (pareto_df["diversity_label"] == "div_on")
        ]

        for user_id in [1, 97]:
            part = df[df["user_id"] == user_id]

            ax.scatter(
                part[OBJECTIVE_X],
                part[OBJECTIVE_Y],
                alpha=0.7,
                label=f"User {user_id}"
            )

        ax.set_title(algorithm.upper())
        ax.set_xlabel(OBJECTIVE_X)
        ax.grid(True)
        ax.legend()

    axes[0].set_ylabel(OBJECTIVE_Y)

    fig.suptitle("User Comparison - Pareto Fronts")
    fig.tight_layout()

    plt.savefig(
        f"{PLOTS_DIR}/user_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

def plot_hypervolume_convergence(history_df):
    df = history_df[
        (history_df["user_id"] == 1) &
        (history_df["diversity_label"] == "div_on")
    ]

    plt.figure()

    for algorithm in df["algorithm"].unique():
        part = df[df["algorithm"] == algorithm]
        plt.plot(part["generation"], part["hypervolume"], label=algorithm.upper())

    plt.xlabel("Generation")
    plt.ylabel("Hypervolume")
    plt.title("Convergence Curve - Hypervolume vs Generation")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/hypervolume_convergence.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_diversity_impact(pareto_df):
    marker_map = {
        "div_on": "o",
        "div_off": "x"
    }

    for algorithm in ["nsga2", "spea2"]:
        df = pareto_df[
            (pareto_df["algorithm"] == algorithm) &
            (pareto_df["user_id"] == 1)
        ]

        plt.figure()

        for label in ["div_off", "div_on"]:
            part = df[df["diversity_label"] == label]

            plt.scatter(
                part["diversity"],
                part["preference"],
                alpha=0.8,
                label=label,
                marker=marker_map[label]
            )

        plt.xlabel("Distinct Food Group Count")
        plt.ylabel("Preference")
        plt.title(f"Diversity Impact - {algorithm.upper()}")
        plt.legend()
        plt.grid(True)

        plt.savefig(
            f"{PLOTS_DIR}/diversity_impact_{algorithm}.png",
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

def main():
    ensure_plots_dir()

    pareto_df = pd.read_csv(PARETO_FILE)
    history_df = pd.read_csv(HISTORY_FILE)

    reference_point = compute_reference_point(history_df)
    history_df = add_hypervolume(history_df, reference_point)

    plot_pareto_per_algorithm(pareto_df)
    plot_algorithm_overlay(pareto_df)
    plot_user_comparison(pareto_df)
    plot_hypervolume_convergence(history_df)
    plot_diversity_impact(pareto_df)

    print("Saved plots:")
    print("plots/pareto_nsga2.png")
    print("plots/pareto_spea2.png")
    print("plots/algorithm_comparison_overlay.png")
    print("plots/user_comparison.png")
    print("plots/hypervolume_convergence.png")
    print("plots/diversity_impact_nsga2.png")
    print("plots/diversity_impact_spea2.png")

    print("Saved CSV:")
    print("results/hypervolume_reference_point.csv")
    print("results/history_all_hv.csv")
    print("results/summary_hypervolume.csv")


if __name__ == "__main__":
    main()