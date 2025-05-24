import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from pathlib import Path

# === 1. Load experimental limits from Excel ===
df_exp = pd.read_excel("lux_zeplin.xlsx", sheet_name="1").sort_values("m_exp").reset_index(drop=True)
mass_exp = df_exp["m_exp"].values
sigma_exp = df_exp["sigma_exp"].values
sigma_interp = PchipInterpolator(mass_exp, sigma_exp)

def get_sigma_limit(m):
    return sigma_interp(m) if mass_exp.min() <= m <= mass_exp.max() else np.nan

# === 2. Read model data from CompHEP output ===
input_folder = "./example_data_direct_detection/150"
folder_name = os.path.basename(input_folder)

model_rows = []
for filename in os.listdir(input_folder):
    if not filename.endswith(".txt"):
        continue

    try:
        m_val = float(filename.replace(".txt", ""))
    except ValueError:
        continue

    with open(os.path.join(input_folder, filename), "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 3:
                continue

            lam, sin_theta, sigma_model = parts[:3]
            if sigma_model.lower() in {"-nan", "nan"}:
                continue

            try:
                model_rows.append({
                    "m_hi": m_val,
                    "lambda": float(lam),
                    "sin": float(sin_theta),
                    "sigma_model": float(sigma_model)
                })
            except ValueError:
                continue

df_model = pd.DataFrame(model_rows).sort_values(["m_hi", "lambda", "sin"]).reset_index(drop=True)
print(f"Read {len(df_model)} rows from '{folder_name}'.")

# === 3. Filter data based on experimental constraint ===
filtered_rows = []

for (m_val, lam_val), group in df_model.groupby(["m_hi", "lambda"]):
    sigma_limit = get_sigma_limit(m_val)

    if pd.isna(sigma_limit):
        chosen_sin = 0.0
    else:
        passed = group[group["sigma_model"] <= sigma_limit]

        if passed.empty:
            chosen_sin = 0.0
        else:
            positive = passed[passed["sin"] > 0]
            negative = passed[passed["sin"] < 0]

            if not positive.empty and len(positive) > len(negative):
                chosen_sin = positive["sin"].max()
            elif not negative.empty:
                chosen_sin = abs(negative["sin"].min())
            else:
                chosen_sin = 0.0

    filtered_rows.append({
        "m_hi": m_val,
        "lambda": lam_val,
        "sin": chosen_sin
    })

df_filtered = pd.DataFrame(filtered_rows).sort_values(["m_hi", "lambda"]).reset_index(drop=True)
print(f"Final dataset: {len(df_filtered)} rows (1 per (m, lambda) pair).")

# === 4. Visualize as 3D plot ===
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
ax.scatter(df_filtered["m_hi"], df_filtered["lambda"], df_filtered["sin"],
           color="blue", marker="^", s=20, alpha=0.9 )
ax.set_xlabel("m_hi")
ax.set_ylabel("lambda")
ax.set_zlabel("sin(theta)")
ax.set_title(f"Filtered results from folder '{folder_name}'")
ax.legend()
plt.show()

# === 5. Write to Excel ===
output_file = "filtered_results.xlsx"
output_path = Path(output_file)

if output_path.exists():
    writer = pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace")
else:
    writer = pd.ExcelWriter(output_path, engine="openpyxl", mode="w")  # без if_sheet_exists!

with writer:
    df_filtered.to_excel(writer, sheet_name=folder_name, index=False)
