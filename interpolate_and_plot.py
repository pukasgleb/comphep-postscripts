import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D

# === Configuration parameters ===
sheet_name = "500"              # Excel sheet name corresponding to radion mass
grid_size = 50                  # Resolution of interpolation grid
outlier_low = 0.01              # Lower quantile for outlier removal
outlier_high = 0.99             # Upper quantile for outlier removal
smoothing_sigma = 1             # Gaussian smoothing strength
sin_threshold = 0.20            # Max allowed value for sin(theta) in plot

# === 1. Load filtered data ===
df = pd.read_excel("filtered_results.xlsx", sheet_name=sheet_name)

# Remove outliers based on quantiles
q_low = df["sin"].quantile(outlier_low)
q_high = df["sin"].quantile(outlier_high)
df_clean = df[(df["sin"] >= q_low) & (df["sin"] <= q_high)].reset_index(drop=True)

# === 2. Create regular interpolation grid ===
mass_range = np.linspace(df_clean["m_hi"].min(), df_clean["m_hi"].max(), grid_size)
lambda_range = np.linspace(df_clean["lambda"].min(), df_clean["lambda"].max(), grid_size)
X, Y = np.meshgrid(mass_range, lambda_range)

# === 3. Interpolate sin(theta) over the grid ===
points = df_clean[["m_hi", "lambda"]].values
values = df_clean["sin"].values
Z = griddata(points, values, (X, Y), method='cubic')

# === 4. Apply Gaussian smoothing (optional) ===
Z_smooth = gaussian_filter(Z, sigma=smoothing_sigma)

# === 5. Apply threshold mask ===
Z_masked = np.minimum(Z_smooth, sin_threshold)

# === 6. Plot the interpolated surface ===
fig1 = plt.figure(figsize=(8, 6), dpi=150)
ax1 = fig1.add_subplot(111, projection='3d')
ax1.set_box_aspect([1, 1, 1], zoom=0.95)

surf = ax1.plot_surface(
    X, Y, Z_masked,
    cmap="viridis",
    edgecolor="none",
    alpha=0.9
)

ax1.set_xlabel(r"$m_{\mathrm{hi}}$ [GeV]")
ax1.set_ylabel(r"$\Lambda$ [GeV]")
ax1.set_zlabel(r"$\sin\theta$", labelpad=4)
ax1.set_title(rf"$M_r = {sheet_name}$ GeV")

# Optional: adjust z-axis limit based on mass
if int(sheet_name) == 500:
    ax1.set_zlim(0, 0.1)
elif int(sheet_name) in [150, 100]:
    ax1.set_zlim(0, 0.2)

ax1.xaxis.set_major_locator(MaxNLocator(nbins=6))
ax1.yaxis.set_major_locator(MaxNLocator(nbins=5))
ax1.zaxis.set_major_locator(MaxNLocator(nbins=4))

# === 7. Plot raw filtered data points ===
fig2 = plt.figure()
ax2 = fig2.add_subplot(111, projection='3d')
ax2.scatter(
    df_clean["m_hi"], df_clean["lambda"], df_clean["sin"],
    color="red", marker="o", s=10
)
ax2.set_xlabel(r"$m_{\mathrm{hi}}$ [GeV]")
ax2.set_ylabel(r"$\Lambda$ [GeV]")
ax2.set_zlabel(r"$\sin\theta$")
ax2.set_title(rf"Filtered data points ($M_r = {sheet_name}$ GeV)")

plt.show()
