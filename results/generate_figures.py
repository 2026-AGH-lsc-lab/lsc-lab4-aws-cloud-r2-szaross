#!/usr/bin/env python3
"""Generate all report figures from actual collected lab data."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Data from CloudWatch REPORT lines (Assignment 1 CLI invoke)
# ---------------------------------------------------------------------------
CW_ZIP_INIT = 639.78
CW_ZIP_DURATION = 96.30
CW_CONTAINER_INIT = 2888.32
CW_CONTAINER_DURATION = 79.94

# Scenario A oha cold-start totals (slowest request = cold start)
OHA_ZIP_COLD_TOTAL = 1551.2       # ms
OHA_CONTAINER_COLD_TOTAL = 4112.0  # ms

# DNS+dialup from Scenario A (TLS handshake, first connection only)
DNS_DIALUP = 51.0  # ms

# Estimated Init from oha (total - DNS/dialup - CW Duration)
EST_ZIP_INIT = OHA_ZIP_COLD_TOTAL - DNS_DIALUP - CW_ZIP_DURATION
EST_CONTAINER_INIT = OHA_CONTAINER_COLD_TOTAL - DNS_DIALUP - CW_CONTAINER_DURATION

# Server-side query time from assignment-1 curl responses
QUERY_TIME_FARGATE = 24.17
QUERY_TIME_EC2 = 23.53
QUERY_TIME_AVG = (QUERY_TIME_FARGATE + QUERY_TIME_EC2) / 2

# ---------------------------------------------------------------------------
# Scenario B — oha data (ALL environments now valid, [200])
# ---------------------------------------------------------------------------
SCENARIO_B = {
    "Lambda zip\nc=5":       {"p50": 98,   "p95": 118,  "p99": 138},
    "Lambda zip\nc=10":      {"p50": 96,   "p95": 119,  "p99": 147},
    "Lambda ctr\nc=5":       {"p50": 94,   "p95": 113,  "p99": 136},
    "Lambda ctr\nc=10":      {"p50": 93,   "p95": 112,  "p99": 151},
    "Fargate\nc=10":         {"p50": 798,  "p95": 1084, "p99": 1192},
    "Fargate\nc=50":         {"p50": 3914, "p95": 4202, "p99": 4305},
    "EC2\nc=10":             {"p50": 209,  "p95": 272,  "p99": 320},
    "EC2\nc=50":             {"p50": 992,  "p95": 1346, "p99": 1581},
}

# ---------------------------------------------------------------------------
# Scenario C — oha data (burst from zero)
# ---------------------------------------------------------------------------
SCENARIO_C = {
    "Lambda zip\nc=10":      {"p50": 100,  "p95": 1158, "p99": 1434},
    "Lambda ctr\nc=10":      {"p50": 95,   "p95": 974,  "p99": 1245},
    "Fargate\nc=50":         {"p50": 3898, "p95": 4200, "p99": 4304},
    "EC2\nc=50":             {"p50": 953,  "p95": 1204, "p99": 1451},
}

# ---------------------------------------------------------------------------
# Cost constants (us-east-1)
# ---------------------------------------------------------------------------
LAMBDA_REQ_COST = 0.20 / 1_000_000
LAMBDA_GBSEC_COST = 0.0000166667
LAMBDA_MEMORY_GB = 0.5
LAMBDA_DURATION_S = QUERY_TIME_AVG / 1000.0

FARGATE_VCPU_HOURLY = 0.04048
FARGATE_GB_HOURLY = 0.004445
FARGATE_MONTHLY = 0.5 * FARGATE_VCPU_HOURLY * 720 + 1.0 * FARGATE_GB_HOURLY * 720

EC2_HOURLY = 0.0208
EC2_MONTHLY = EC2_HOURLY * 720

SECONDS_PER_MONTH = 30 * 24 * 3600


def fig1_latency_decomposition():
    """Stacked bar chart: cold start decomposition."""
    categories = [
        "Lambda Zip\n(Cold Start)",
        "Lambda Container\n(Cold Start)",
        "Lambda Zip\n(Warm)",
        "Lambda Container\n(Warm)",
    ]
    network = [DNS_DIALUP, DNS_DIALUP, 5.0, 5.0]
    init = [EST_ZIP_INIT, EST_CONTAINER_INIT, 0, 0]
    handler = [CW_ZIP_DURATION, CW_CONTAINER_DURATION,
               QUERY_TIME_AVG, QUERY_TIME_AVG]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(categories))
    width = 0.5

    ax.bar(x, network, width, label="Network / TLS (~51 ms cold, ~5 ms warm)",
           color="#4C72B0")
    ax.bar(x, init, width, bottom=network, label="Init Duration", color="#E5AE38")
    bottoms = [n + i for n, i in zip(network, init)]
    ax.bar(x, handler, width, bottom=bottoms, label="Handler Duration", color="#55A868")

    totals = [n + i + h for n, i, h in zip(network, init, handler)]
    for i, total in enumerate(totals):
        ax.text(i, total + 40, f"{total:.0f} ms", ha="center",
                fontweight="bold", fontsize=10)
    for i, val in enumerate(init):
        if val > 0:
            ax.text(i, network[i] + val / 2, f"{val:.0f} ms",
                    ha="center", va="center", fontsize=9)
    for i, val in enumerate(handler):
        if val > 30:
            ax.text(i, bottoms[i] + val / 2, f"{val:.1f} ms",
                    ha="center", va="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_title("Figure 1: Lambda Latency Decomposition — Cold Start vs Warm",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.set_ylim(0, max(totals) * 1.12)

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, "fig1_latency_decomposition.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def fig2_cost_vs_rps():
    """Lambda cost vs. always-on cost as a function of average RPS."""
    rps = np.linspace(0, 100, 500)

    per_req_cost = LAMBDA_REQ_COST + LAMBDA_DURATION_S * LAMBDA_MEMORY_GB * LAMBDA_GBSEC_COST
    lambda_monthly = rps * SECONDS_PER_MONTH * per_req_cost

    breakeven_ec2 = EC2_MONTHLY / (SECONDS_PER_MONTH * per_req_cost)
    breakeven_fargate = FARGATE_MONTHLY / (SECONDS_PER_MONTH * per_req_cost)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rps, lambda_monthly, color="#E5AE38", linewidth=2,
            label="Lambda (on-demand)")
    ax.axhline(y=FARGATE_MONTHLY, color="#55A868", linestyle="--",
               linewidth=2, label=f"Fargate (always-on) = ${FARGATE_MONTHLY:.2f}/mo")
    ax.axhline(y=EC2_MONTHLY, color="#4C72B0", linestyle="-.",
               linewidth=2, label=f"EC2 t3.small (always-on) = ${EC2_MONTHLY:.2f}/mo")

    ax.axvline(x=breakeven_ec2, color="red", linestyle=":", alpha=0.7)
    ax.annotate(f"Break-even (EC2): {breakeven_ec2:.1f} RPS",
                xy=(breakeven_ec2, EC2_MONTHLY),
                xytext=(breakeven_ec2 + 5, EC2_MONTHLY + 20),
                fontsize=10, color="red",
                arrowprops=dict(arrowstyle="->", color="red"))

    ax.set_xlabel("Average Requests Per Second (RPS)", fontsize=11)
    ax.set_ylabel("Monthly Cost (USD)", fontsize=11)
    ax.set_title("Figure 2: Monthly Cost vs. Request Rate",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper left")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, max(lambda_monthly[-1], 220))

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, "fig2_cost_vs_rps.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}  (break-even EC2={breakeven_ec2:.1f}, Fargate={breakeven_fargate:.1f} RPS)")


def fig3_burst_comparison():
    """Grouped bar chart: all environments under burst (Scenario C)."""
    envs = list(SCENARIO_C.keys())
    metrics = ["p50", "p95", "p99"]
    colors = ["#4C72B0", "#E5AE38", "#C44E52"]

    x = np.arange(len(envs))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    for j, m in enumerate(metrics):
        vals = [SCENARIO_C[e][m] for e in envs]
        bars = ax.bar(x + j * width, vals, width, label=m, color=colors[j])
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 40,
                    f"{bar.get_height():.0f}", ha="center", fontsize=8)

    ax.axhline(y=500, color="red", linestyle="--", linewidth=1.5,
               label="SLO: p99 < 500 ms")

    ax.set_xticks(x + width)
    ax.set_xticklabels(envs, fontsize=10)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_title("Figure 3: Burst from Zero — Latency Distribution (Scenario C)",
                 fontsize=12, fontweight="bold")
    ax.legend()

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, "fig3_burst_comparison.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def fig4_warm_throughput():
    """Grouped bar chart: all environments warm throughput (Scenario B)."""
    envs = list(SCENARIO_B.keys())
    metrics = ["p50", "p95", "p99"]
    colors = ["#4C72B0", "#E5AE38", "#C44E52"]

    x = np.arange(len(envs))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 6))
    for j, m in enumerate(metrics):
        vals = [SCENARIO_B[e][m] for e in envs]
        ax.bar(x + j * width, vals, width, label=m, color=colors[j])

    ax.axhline(y=500, color="red", linestyle="--", linewidth=1.5,
               alpha=0.6, label="SLO: p99 < 500 ms")

    ax.set_xticks(x + width)
    ax.set_xticklabels(envs, fontsize=9)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_title("Figure 4: Warm Steady-State Latency (Scenario B)",
                 fontsize=12, fontweight="bold")
    ax.legend()

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, "fig4_warm_throughput.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


if __name__ == "__main__":
    fig1_latency_decomposition()
    fig2_cost_vs_rps()
    fig3_burst_comparison()
    fig4_warm_throughput()
    print("\nAll figures generated.")
