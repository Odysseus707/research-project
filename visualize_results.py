import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import os
import ast
import argparse

AVAILABLE_COLOR = "#2ca02c"  # green
MISSING_COLOR = "#d62728"    # red

# ----------------------------
# Helpers
# ----------------------------
def build_args():
    parser = argparse.ArgumentParser(description="Create segmented acquisition visuals from transfer logs.")
    parser.add_argument("--log-file", default="node_transfers_log.txt", help="Path to transfer log file.")
    parser.add_argument("--node-id", type=int, default=0, help="Node id to visualize.")
    parser.add_argument(
        "--modalities",
        default="precipitation,temp_max,temp_min,wind",
        help="Comma-separated modalities to visualize (order preserved).",
    )
    parser.add_argument("--output-dir", default="results", help="Directory to write PNGs and GIF.")
    parser.add_argument("--interval-ms", type=int, default=900, help="GIF frame interval in milliseconds.")
    return parser.parse_args()


def extract_message(raw_line):
    line = raw_line.strip()
    parts = line.split(" | ", 2)
    return parts[2] if len(parts) == 3 else line


def parse_list_from_message(message):
    start = message.find("[")
    end = message.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    return ast.literal_eval(message[start:end + 1])


def parse_selected_line(message):
    modality_match = re.search(r"Modality=([^|]+)", message)
    timestamps_match = re.search(r"Timestamps=\[.*\]", message)
    if not modality_match or not timestamps_match:
        return None, []
    modality = modality_match.group(1).strip()
    timestamps = parse_list_from_message(timestamps_match.group(0))
    return modality, timestamps


def snapshot_from_state(round_label, total_timestamps, modality_coverage, modalities_to_show):
    total_count = len(total_timestamps)
    available_counts = []
    missing_counts = []
    for modality in modalities_to_show:
        available = len(modality_coverage[modality].intersection(total_timestamps))
        available_counts.append(available)
        missing_counts.append(max(total_count - available, 0))
    return {
        "round_label": round_label,
        "total_count": total_count,
        "available_counts": available_counts,
        "missing_counts": missing_counts,
    }


def draw_segmented_bar(ax, snapshot, modalities_to_show, node_id_to_visualize):
    x = range(len(modalities_to_show))
    ax.bar(x, snapshot["available_counts"], color=AVAILABLE_COLOR, label="Available")
    ax.bar(
        x,
        snapshot["missing_counts"],
        bottom=snapshot["available_counts"],
        color=MISSING_COLOR,
        label="Missing",
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(modalities_to_show, rotation=15)
    ax.set_ylabel("Data points (timestamps)")
    ax.set_ylim(0, max(snapshot["total_count"], 1))
    ax.set_title(
        f"Node {node_id_to_visualize} | {snapshot['round_label']} | "
        f"Total timestamps={snapshot['total_count']}"
    )
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.25)


def main():
    args = build_args()
    log_file = args.log_file
    node_id_to_visualize = args.node_id
    modalities_to_show = [m.strip() for m in args.modalities.split(",") if m.strip()]
    output_dir = args.output_dir
    interval_ms = max(args.interval_ms, 100)

    if not modalities_to_show:
        raise ValueError("At least one modality must be provided via --modalities.")

    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_round = None
    inside_target_node = False
    first_seen_target = False

    pre_features = []
    pre_timestamps = set()
    post_timestamps = None
    selected_for_block = []

    modality_coverage = {m: set() for m in modalities_to_show}
    total_timestamps = set()
    snapshots = []

    def flush_target_block():
        nonlocal pre_features, pre_timestamps, post_timestamps, selected_for_block
        nonlocal first_seen_target, total_timestamps
        nonlocal inside_target_node, current_round

        if not inside_target_node:
            return

        if not first_seen_target and pre_timestamps:
            total_timestamps = set(pre_timestamps)
            for feat in pre_features:
                if feat in modality_coverage:
                    modality_coverage[feat] = set(pre_timestamps)
            snapshots.append(
                snapshot_from_state(
                    "Round 0 (pre-transfer)",
                    total_timestamps,
                    modality_coverage,
                    modalities_to_show,
                )
            )
            first_seen_target = True

        for modality, ts_values in selected_for_block:
            if modality in modality_coverage:
                modality_coverage[modality].update(ts_values)

        if post_timestamps is not None:
            total_timestamps = set(post_timestamps)

        if first_seen_target and current_round is not None:
            snapshots.append(
                snapshot_from_state(
                    f"Round {current_round} (post-transfer)",
                    total_timestamps,
                    modality_coverage,
                    modalities_to_show,
                )
            )

        pre_features = []
        pre_timestamps = set()
        post_timestamps = None
        selected_for_block = []

    for raw in lines:
        msg = extract_message(raw)

        round_match = re.match(r"=+ ROUND (\d+) =+", msg)
        if round_match:
            flush_target_block()
            inside_target_node = False
            current_round = int(round_match.group(1))
            continue

        node_match = re.match(r"Node (\d+)", msg)
        if node_match:
            flush_target_block()
            inside_target_node = int(node_match.group(1)) == node_id_to_visualize
            continue

        if not inside_target_node:
            continue

        if msg.startswith("PRE-TRANSFER FEATURES:"):
            pre_features = parse_list_from_message(msg)
        elif msg.startswith("PRE-TRANSFER TIMESTAMPS:"):
            pre_timestamps = set(parse_list_from_message(msg))
        elif msg.startswith("SELECTED |"):
            modality, ts_values = parse_selected_line(msg)
            if modality is not None:
                selected_for_block.append((modality, ts_values))
        elif msg.startswith("POST-TRANSFER TIMESTAMPS:"):
            post_timestamps = set(parse_list_from_message(msg))

    flush_target_block()

    if not snapshots:
        raise ValueError(
            f"No snapshots generated for node {node_id_to_visualize}. "
            "Check node id or log format."
        )

    print(f"Generated {len(snapshots)} snapshots for node {node_id_to_visualize}.")
    os.makedirs(output_dir, exist_ok=True)

    for idx, snap in enumerate(snapshots):
        fig, ax = plt.subplots(figsize=(9, 5))
        draw_segmented_bar(ax, snap, modalities_to_show, node_id_to_visualize)
        fig.tight_layout()
        png_path = os.path.join(output_dir, f"node{node_id_to_visualize}_segmented_round_{idx}.png")
        fig.savefig(png_path)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))

    def update(frame_idx):
        ax.clear()
        draw_segmented_bar(ax, snapshots[frame_idx], modalities_to_show, node_id_to_visualize)
        return [ax]

    ani = animation.FuncAnimation(fig, update, frames=len(snapshots), interval=interval_ms)
    gif_path = os.path.join(output_dir, f"node{node_id_to_visualize}_segmented_acquisition.gif")
    ani.save(gif_path, writer="pillow")
    plt.close(fig)

    print(f"Saved segmented bar GIF: {gif_path}")
    print(f"Saved per-round PNGs in: {output_dir}")


if __name__ == "__main__":
    main()