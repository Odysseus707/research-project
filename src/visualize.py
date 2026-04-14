from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RESULTS_DIR = Path("results")
PLOTS_DIR = Path("plots")
RESULTS_SUFFIX = "_experiment_results.csv"
PARAM_COLUMNS = [
    "num_requests",
    "num_nodes",
    "data_uniformity",
    "seed",
    "topology_type",
    "balanced_tree_branching_factor",
]
SUMMARY_COLUMNS = PARAM_COLUMNS + [
    "algorithm",
    "time_taken",
    "fairness_index",
    "successful_calculation_overall",
    "failed_calculation_count",
]
ALGORITHM_ORDER = ["proposed", "proposed_fast", "random", "ilp"]
ALGORITHM_LABELS = {
    "proposed": "Proposed",
    "proposed_fast": "Proposed Fast",
    "random": "Random",
    "ilp": "ILP",
}
ALGORITHM_COLORS = {
    "proposed": "#1b9e77",
    "proposed_fast": "#66a61e",
    "random": "#d95f02",
    "ilp": "#7570b3",
}
ALGORITHM_MARKERS = {
    "proposed": "o",
    "proposed_fast": "D",
    "random": "s",
    "ilp": "^",
}
ALGORITHM_ALPHAS = {
    "proposed": 1.0,
    "proposed_fast": 1.0,
    "random": 0.5,
    "ilp": 0.5,
}


def _find_latest_results_path() -> Path:
    candidates = sorted(
        RESULTS_DIR.glob(f"*{RESULTS_SUFFIX}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No experiment result files matching *{RESULTS_SUFFIX} were found in {RESULTS_DIR}."
        )
    return candidates[0]


def _derive_output_dir(csv_path: str | Path) -> Path:
    csv_path = Path(csv_path)
    prefix = csv_path.name.removesuffix(RESULTS_SUFFIX)
    return PLOTS_DIR / f"{prefix}_plots"


def load_experiment_results(csv_path: str | Path | None = None) -> pd.DataFrame:
    csv_path = _find_latest_results_path() if csv_path is None else Path(csv_path)
    csv_path = Path(csv_path)
    return pd.read_csv(csv_path)


def ensure_output_dir(output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def prepare_request_metrics_longform(df: pd.DataFrame) -> pd.DataFrame:
    success_column = (
        "successful_calculation"
        if "successful_calculation" in df.columns
        else "qos"
    )
    return (
        df[PARAM_COLUMNS + ["algorithm", "request_idx", "cost", success_column]]
        .rename(
            columns={
                "cost": "avg_cost_per_request",
                success_column: "avg_successful_calculation",
            }
        )
        .copy()
    )


def prepare_run_metrics_longform(df: pd.DataFrame) -> pd.DataFrame:
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

    return (
        df[available_summary_columns]
        .drop_duplicates()
        .rename(
            columns={
                "time_taken": "avg_time_taken",
                "fairness_index": "avg_fairness",
                "successful_calculation_overall": (
                    "avg_successful_calculation_overall"
                ),
                "failed_calculation_count": "avg_failed_calculation_count",
            }
        )
        .copy()
    )


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

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    for algorithm in ALGORITHM_ORDER:
        algorithm_df = plot_df[plot_df["algorithm"] == algorithm]
        if algorithm_df.empty:
            continue
        sns.lineplot(
            data=algorithm_df,
            x=x_column,
            y=y_column,
            estimator="mean",
            errorbar=None,
            marker=ALGORITHM_MARKERS[algorithm],
            linewidth=2.2,
            color=ALGORITHM_COLORS[algorithm],
            alpha=ALGORITHM_ALPHAS[algorithm],
            label=ALGORITHM_LABELS.get(algorithm, algorithm.title()),
            ax=ax,
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
    output_dir: str | Path,
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
    output_dir: str | Path,
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
    output_dir: str | Path,
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
    output_dir: str | Path,
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
    output_dir: str | Path,
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
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=plot_df,
        x=group_by,
        y="avg_failed_calculation_count",
        hue="algorithm",
        hue_order=ALGORITHM_ORDER,
        palette=ALGORITHM_COLORS,
        estimator="mean",
        errorbar=None,
        ax=ax,
    )

    ax.set_title("Failed Calculations Per Experiment")
    ax.set_xlabel(group_by.replace("_", " ").title())
    ax.set_ylabel("Average Failed Calculations")
    legend = ax.get_legend()
    if legend is not None:
        for text in legend.texts:
            label = text.get_text()
            text.set_text(ALGORITHM_LABELS.get(label, label.title()))
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
    csv_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    group_by: str = "num_nodes",
    filters: dict[str, object] | None = None,
) -> list[Path]:
    resolved_csv_path = _find_latest_results_path() if csv_path is None else Path(csv_path)
    resolved_output_dir = (
        _derive_output_dir(resolved_csv_path)
        if output_dir is None
        else Path(output_dir)
    )
    df = load_experiment_results(resolved_csv_path)
    request_metrics = prepare_request_metrics_longform(df)
    run_metrics = prepare_run_metrics_longform(df)
    created_plots = [
        plot_avg_cost_per_request(
            request_metrics, resolved_output_dir, group_by, filters
        ),
        plot_successful_calculation_comparison(
            request_metrics, resolved_output_dir, group_by, filters
        ),
    ]

    if not run_metrics.empty:
        created_plots.append(
            plot_runtime_comparison(
                run_metrics, resolved_output_dir, group_by, filters
            )
        )
        created_plots.append(
            plot_fairness_comparison(
                run_metrics, resolved_output_dir, group_by, filters
            )
        )
        created_plots.append(
            plot_failed_calculation_bar(
                run_metrics, resolved_output_dir, group_by, filters
            )
        )

    return created_plots


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualize experiment results for algorithm comparisons."
    )
    parser.add_argument(
        "--csv-path",
        default=None,
        help="Path to the experiment results CSV file. Defaults to the latest file in results/.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where plot images will be written. Defaults to plots/foo_plots matching the CSV.",
    )
    parser.add_argument(
        "--group-by",
        default="num_nodes",
        choices=[
            "num_requests",
            "num_nodes",
            "data_uniformity",
            "seed",
            "balanced_tree_branching_factor",
        ],
        help="Parameter to place on the x-axis.",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        help=(
            "Restrict plots to matching rows, for example "
            "--filter balanced_tree_branching_factor=2."
        ),
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
