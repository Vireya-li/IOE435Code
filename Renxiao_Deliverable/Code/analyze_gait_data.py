"""
Offline Gait Analysis — IOE 435 Final Project, Group 11
Reads IMU CSV data, detects steps, generates figures for Lesson Plan.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

DATA_DIR = r"C:\Users\asus\OneDrive\Desktop\IOE 435\Project\Data"
OUT_DIR  = r"C:\Users\asus\OneDrive\Desktop\IOE 435\Project\Figures"
os.makedirs(OUT_DIR, exist_ok=True)

FILES = {
    "Walking (with pause) T1": "2026_03_31_11h_25m_31s_20Ft_Pause_T1.csv",
    "Walking (with pause) T2": "2026_03_31_11h_26m_05s_20Ft_Pause_T2.csv",
    "Skipping":                "2026_03_31_11h_29m_20s_20ft_Skipping_T1.csv",
    "High Knees T1":           "2026_03_31_11h_30m_41s_20ft_HighKnees_T1.csv",
    "High Knees T2":           "2026_03_31_11h_31m_23s_20ft_HighKnees_T2.csv",
}

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 18,
    "axes.labelsize": 15,
    "figure.facecolor": "white",
})


def load(name):
    path = os.path.join(DATA_DIR, FILES[name])
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = df.columns.str.strip().str.rstrip(",")
    df = df.loc[:, ~df.columns.duplicated()]
    if "" in df.columns:
        df = df.drop(columns=[""])
    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1000.0
    return df


def detect_steps(df, height=80, distance=25):
    gz = df["gyro_z"].values
    peaks, props = find_peaks(np.abs(gz), height=height, distance=distance)
    return peaks


# =========================================================================
# Figure 1 — Single walking trial with step markers (main demo figure)
# =========================================================================
df = load("Walking (with pause) T1")
peaks = detect_steps(df, height=60, distance=25)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["time_s"], df["gyro_z"], color="#00b4d8", linewidth=1.5, label="Gyro Z (°/s)")
ax.scatter(df["time_s"].iloc[peaks], df["gyro_z"].iloc[peaks],
           color="#ff6b6b", s=80, zorder=5, label=f"Steps detected: {len(peaks)}")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Angular Velocity (°/s)")
ax.set_title("Walking 20 ft — Each Red Dot Is One Step!")
ax.legend(fontsize=13, loc="upper right")
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig1_walking_steps.png"), dpi=200)
print(f"Figure 1 saved — Walking with {len(peaks)} steps detected")


# =========================================================================
# Figure 2 — Comparison of 3 activities (walking vs skipping vs high knees)
# =========================================================================
activities = [
    ("Walking (with pause) T1", "#00b4d8", 60),
    ("Skipping",                "#ffd166", 80),
    ("High Knees T1",           "#ef476f", 80),
]

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)
for ax, (name, color, thresh) in zip(axes, activities):
    df_a = load(name)
    pks = detect_steps(df_a, height=thresh, distance=25)
    ax.plot(df_a["time_s"], df_a["gyro_z"], color=color, linewidth=1.3)
    ax.scatter(df_a["time_s"].iloc[pks], df_a["gyro_z"].iloc[pks],
               color="#ff6b6b", s=50, zorder=5)
    short = name.split(" T")[0]
    ax.set_title(f"{short} — {len(pks)} steps", fontsize=15, fontweight="bold")
    ax.set_ylabel("°/s")
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Time (seconds)")
fig.suptitle("How Does the Signal Change with Different Movements?",
             fontsize=18, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig2_activity_comparison.png"), dpi=200,
            bbox_inches="tight")
print("Figure 2 saved — Activity comparison")


# =========================================================================
# Figure 3 — Zoomed-in view: 3 seconds of walking (show individual peaks)
# =========================================================================
df = load("Walking (with pause) T1")
t = df["time_s"].values
gz = df["gyro_z"].values
mask = (t >= 2) & (t <= 7)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(t[mask], gz[mask], color="#00b4d8", linewidth=2.5)
pks_local = detect_steps(df[mask].reset_index(drop=True), height=60, distance=25)
t_mask = t[mask]
gz_mask = gz[mask]
ax.scatter(t_mask[pks_local], gz_mask[pks_local], color="#ff6b6b", s=120, zorder=5)
for i, pk in enumerate(pks_local):
    ax.annotate(f"Step {i+1}", (t_mask[pk], gz_mask[pk]),
                textcoords="offset points", xytext=(0, 18),
                fontsize=12, fontweight="bold", color="#ff6b6b",
                ha="center")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Angular Velocity (°/s)")
ax.set_title("Zoomed In — Can You Count the Steps?")
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig3_zoomed_steps.png"), dpi=200)
print("Figure 3 saved — Zoomed-in steps")


# =========================================================================
# Figure 4 — Accelerometer vs Gyroscope comparison
# =========================================================================
df = load("Walking (with pause) T1")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

ax1.plot(df["time_s"], df["accl_x"], label="X", alpha=0.8)
ax1.plot(df["time_s"], df["accl_y"], label="Y", alpha=0.8)
ax1.plot(df["time_s"], df["accl_z"], label="Z", alpha=0.8)
ax1.set_ylabel("Acceleration (g)")
ax1.set_title("Accelerometer — Measures How Fast You Speed Up or Slow Down")
ax1.legend(loc="upper right")
ax1.grid(True, alpha=0.3)

ax2.plot(df["time_s"], df["gyro_x"], label="X", alpha=0.8)
ax2.plot(df["time_s"], df["gyro_y"], label="Y", alpha=0.8)
ax2.plot(df["time_s"], df["gyro_z"], label="Z", alpha=0.8)
ax2.set_xlabel("Time (seconds)")
ax2.set_ylabel("Angular Velocity (°/s)")
ax2.set_title("Gyroscope — Measures How Fast Your Foot Rotates")
ax2.legend(loc="upper right")
ax2.grid(True, alpha=0.3)

fig.suptitle("Two Types of Motion Sensors on Your Ankle",
             fontsize=17, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig4_accl_vs_gyro.png"), dpi=200,
            bbox_inches="tight")
print("Figure 4 saved — Accelerometer vs Gyroscope")


# =========================================================================
# Figure 5 — Repeatability: two trials of same activity
# =========================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=False)

for ax, trial in zip([ax1, ax2], ["High Knees T1", "High Knees T2"]):
    df_t = load(trial)
    pks = detect_steps(df_t, height=80, distance=25)
    ax.plot(df_t["time_s"], df_t["gyro_z"], color="#ef476f", linewidth=1.3)
    ax.scatter(df_t["time_s"].iloc[pks], df_t["gyro_z"].iloc[pks],
               color="#06d6a0", s=60, zorder=5)
    ax.set_title(f"{trial} — {len(pks)} steps detected", fontsize=14, fontweight="bold")
    ax.set_ylabel("°/s")
    ax.grid(True, alpha=0.3)

ax2.set_xlabel("Time (seconds)")
fig.suptitle("Same Movement, Twice — Does the Pattern Look Similar?",
             fontsize=17, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig5_repeatability.png"), dpi=200,
            bbox_inches="tight")
print("Figure 5 saved — Repeatability comparison")

print(f"\nAll figures saved to: {OUT_DIR}")
