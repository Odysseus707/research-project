from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_RESULTS_PATH = Path("experiment_results.csv")
DEFAULT_OUTPUT_DIR = Path("plots")
PARAM_COLUMNS = [
    "num_requests",
    "num_nodes",
    "data_uniformity",
    "seed",
    "topology_type",
]
SUMMARY_COLUMNS = PARAM_COLUMNS + [
    "algorithm",
    "time_taken",
    "fairness_index",
    "successful_calculation_overall",
    "failed_calculation_count",
]
ALGORITHM_ORDER = ["proposed", "random", "ilp"]
ALGORITHM_LABELS = {
    "proposed": "Proposed",
    "random": "Random",
    "ilp": "ILP",
}
ALGORITHM_COLORS = {
    "proposed": "#1b9e77",
    "random": "#d95f02",
    "ilp": "#7570b3",
}


def load_experiment_results(csv_path: str | Path = DEFAULT_RESULTS_PATH) -> pd.DataFrame:
    csv_path = Path(csv_path)
    lines = csv_path.read_text().splitlines()

    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("algorithm,"):
            header_idx = idx
            break

    if header_idx is None:
        raise ValueError(
            f"Could not find CSV header in {csv_path}. "
            "Expected a line starting with 'algorithm,'."
        )

    return pd.read_csv(csv_path, skiprows=header_idx)


def ensure_output_dir(output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def aggregate_request_metrics(df: pd.DataFrame) -> pd.DataFrame:
    success_column = (
        "successful_calculation"
        if "successful_calculation" in df.columns
        else "qos"
    )
    grouped = (
        df.groupby(PARAM_COLUMNS + ["algorithm"], dropna=False)
        .agg(
            avg_cost_per_request=("cost", "mean"),
            avg_successful_calculation=(success_column, "mean"),
            request_count=("request_idx", "count"),
        )
        .reset_index()
    )
    return grouped


def aggregate_run_metrics(df: pd.DataFrame) -> pd.DataFrame:
    available_summary_columns = [
        column for column in SUMMARY_COLUMNS if column in df.columns
    ]
    missing = {
        "time_taken",
        "fairness_index",
        "successful_calculation_overall",
        "failed_calculation_count",
    } - set(df.columns)
    if missing:
        return pd.DataFrame()

    grouped = (
        df[available_summary_columns]
        .drop_duplicates()
        .groupby(PARAM_COLUMNS + ["algorithm"], dropna=False)
        .agg(
            avg_time_taken=("time_taken", "mean"),
            avg_fairness=("fairness_index", "mean"),
            avg_successful_calculation_overall=(
                "successful_calculation_overall",
                "mean",
            ),
            avg_failed_calculation_count=("failed_calculation_count", "mean"),
        )
        .reset_index()
    )
    return grouped


def _apply_algorithm_style(ax: plt.Axes) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(frameon=False)
    ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.8)
    ax.set_axisbelow(True)


def _plot_metric_by_x(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    output_path: Path,
    title: str,
    ylabel: str,
    filters: dict[str, object] | None = None,
) -> Path:
    plot_df = df.copy()
    if filters:
        for column, value in filters.items():
            plot_df = plot_df[plot_df[column] == value]

    if plot_df.empty:
        raise ValueError("No rows matched the requested filters for plotting.")

    fig, ax = plt.subplots(figsize=(10, 6))

    for algorithm in ALGORITHM_ORDER:
        alg_df = plot_df[plot_df["algorithm"] == algorithm].sort_values(x_column)
        if alg_df.empty:
            continue
        ax.plot(
            alg_df[x_column],
            alg_df[y_column],
            marker="o",
            linewidth=2.2,
            markersize=6,
            label=ALGORITHM_LABELS.get(algorithm, algorithm.title()),
            color=ALGORITHM_COLORS.get(algorithm),
        )

    ax.set_title(title)
    ax.set_xlabel(x_column.replace("_", " ").title())
    ax.set_ylabel(ylabel)
    _apply_algorithm_style(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_avg_cost_per_request(
    request_metrics: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> Path:
    output_path = ensure_output_dir(output_dir) / "avg_cost_per_request.png"
    return _plot_metric_by_x(
        request_metrics,
        x_column=group_by,
        y_column="avg_cost_per_request",
        output_path=output_path,
        title="Average Objective Value Per Request",
        ylabel="Average Cost",
        filters=filters,
    )


def plot_runtime_comparison(
    run_metrics: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> Path:
    if run_metrics.empty:
        raise ValueError(
            "Runtime data is unavailable in this CSV. "
            "Re-run the experiments after updating src/main.py."
        )
    output_path = ensure_output_dir(output_dir) / "runtime_comparison.png"
    return _plot_metric_by_x(
        run_metrics,
        x_column=group_by,
        y_column="avg_time_taken",
        output_path=output_path,
        title="Average Runtime Per Experiment",
        ylabel="Time Taken (seconds)",
        filters=filters,
    )


def plot_successful_calculation_comparison(
    request_metrics: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> Path:
    output_path = ensure_output_dir(output_dir) / "successful_calculation_comparison.png"
    return _plot_metric_by_x(
        request_metrics,
        x_column=group_by,
        y_column="avg_successful_calculation",
        output_path=output_path,
        title="Average Successful Calculation Rate",
        ylabel="Success Rate",
        filters=filters,
    )


def plot_fairness_comparison(
    run_metrics: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> Path:
    if run_metrics.empty:
        raise ValueError(
            "Fairness data is unavailable in this CSV. "
            "Re-run the experiments after updating src/main.py."
        )
    output_path = ensure_output_dir(output_dir) / "fairness_comparison.png"
    return _plot_metric_by_x(
        run_metrics,
        x_column=group_by,
        y_column="avg_fairness",
        output_path=output_path,
        title="Average Fairness Index",
        ylabel="Fairness Index",
        filters=filters,
    )


def plot_failed_calculation_bar(
    run_metrics: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> Path:
    if run_metrics.empty:
        raise ValueError(
            "Failed calculation data is unavailable in this CSV. "
            "Re-run the experiments after updating src/main.py."
        )

    plot_df = run_metrics.copy()
    if filters:
        for column, value in filters.items():
            plot_df = plot_df[plot_df[column] == value]

    if plot_df.empty:
        raise ValueError("No rows matched the requested filters for plotting.")

    output_path = ensure_output_dir(output_dir) / "failed_calculation_count.png"
    x_values = sorted(plot_df[group_by].unique())
    x_positions = list(range(len(x_values)))
    bar_width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    for idx, algorithm in enumerate(ALGORITHM_ORDER):
        alg_df = plot_df[plot_df["algorithm"] == algorithm].sort_values(group_by)
        if alg_df.empty:
            continue
        offset = (idx - 1) * bar_width
        positions = [pos + offset for pos in x_positions]
        y_values = []
        for x_value in x_values:
            match = alg_df[alg_df[group_by] == x_value]
            y_values.append(
                float(match["avg_failed_calculation_count"].iloc[0])
                if not match.empty
                else 0.0
            )
        ax.bar(
            positions,
            y_values,
            width=bar_width,
            label=ALGORITHM_LABELS.get(algorithm, algorithm.title()),
            color=ALGORITHM_COLORS.get(algorithm),
        )

    ax.set_title("Failed Calculations Per Experiment")
    ax.set_xlabel(group_by.replace("_", " ").title())
    ax.set_ylabel("Average Failed Calculations")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_values)
    _apply_algorithm_style(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def _parse_filters(filter_args: Iterable[str]) -> dict[str, object]:
    filters: dict[str, object] = {}
    for item in filter_args:
        if "=" not in item:
            raise ValueError(
                f"Invalid filter '{item}'. Expected format like num_requests=50."
            )

        key, raw_value = item.split("=", maxsplit=1)
        value: object = raw_value
        for caster in (int, float):
            try:
                value = caster(raw_value)
                break
            except ValueError:
                continue
        filters[key] = value
    return filters


def create_all_plots(
    csv_path: str | Path = DEFAULT_RESULTS_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> list[Path]:
    df = load_experiment_results(csv_path)
    request_metrics = aggregate_request_metrics(df)
    run_metrics = aggregate_run_metrics(df)
    created_plots = [
        plot_avg_cost_per_request(request_metrics, output_dir, group_by, filters),
        plot_successful_calculation_comparison(
            request_metrics, output_dir, group_by, filters
        ),
    ]

    if not run_metrics.empty:
        created_plots.append(
            plot_runtime_comparison(run_metrics, output_dir, group_by, filters)
        )
        created_plots.append(
            plot_fairness_comparison(run_metrics, output_dir, group_by, filters)
        )
        created_plots.append(
            plot_failed_calculation_bar(run_metrics, output_dir, group_by, filters)
        )

    return created_plots


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualize experiment results for algorithm comparisons."
    )
    parser.add_argument(
        "--csv-path",
        default=str(DEFAULT_RESULTS_PATH),
        help="Path to the experiment results CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where plot images will be written.",
    )
    parser.add_argument(
        "--group-by",
        default="num_nodes",
        choices=["num_requests", "num_nodes", "data_uniformity", "seed"],
        help="Parameter to place on the x-axis.",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        help="Restrict plots to matching rows, for example --filter topology_type=star.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    filters = _parse_filters(args.filter)
    created = create_all_plots(
        csv_path=args.csv_path,
        output_dir=args.output_dir,
        group_by=args.group_by,
        filters=filters,
    )
    for path in created:
        print(f"Created plot: {path}")


if __name__ == "__main__":
    main()
