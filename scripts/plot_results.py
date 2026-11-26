from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

results = Path(__file__).resolve().parent.parent / "results"
files = [
    results / "baseline_5runs_30s.csv",
    results / "qos_5runs_30s.csv",
]
data = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
means = data.groupby(["flow", "condition"]).mean(numeric_only=True)

plots = [
    ("throughput_mbps", "Mean throughput (Mbit/s)", ["voip", "video", "bulk_tcp"]),
    ("jitter_ms", "Mean jitter (ms)", ["voip", "video"]),
    ("loss_pct", "Mean packet loss (%)", ["voip", "video"]),
    ("tcp_retransmits", "Mean TCP retransmissions", ["bulk_tcp"]),
]

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for ax, (metric, title, flows) in zip(axes.flat, plots):
    values = means.loc[
        means.index.get_level_values("flow").isin(flows), metric
    ].unstack("condition").reindex(flows)
    values = values[[name for name in ("baseline", "qos") if name in values.columns]]
    values.plot(kind="bar", ax=ax, rot=0)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Condition")

fig.suptitle("Baseline vs QoS: five concurrent-flow runs")
fig.tight_layout()
output = results / "baseline_vs_qos.png"
fig.savefig(output, dpi=180, bbox_inches="tight")
print("Saved graph to", output)
