# individual_plot_app.py

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.interpolate import PchipInterpolator, UnivariateSpline

# === 1. Class to store file and plot options ===
class FileEntry:
    def __init__(self, filepath):
        self.filepath = filepath
        self.label = os.path.basename(filepath)
        self.subdir = os.path.basename(os.path.dirname(filepath))
        self.method = tk.StringVar(value="None")
        self.poly_degree = tk.StringVar(value="5")
        self.custom_label = tk.StringVar(value="")
        self.xmin = tk.StringVar()
        self.xmax = tk.StringVar()
        self.data_min = None
        self.data_max = None

class IndividualPlotApp:
# === 2. Application GUI ===    
    def __init__(self, root):
        self.root = root
        self.root.title("Curve Approximation Viewer")

        self.log_x = tk.BooleanVar()
        self.log_y = tk.BooleanVar()
        self.files = []

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

        self.setup_controls()

    def setup_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Button(control_frame, text="Add Files", command=self.add_files).pack(pady=5)
        tk.Button(control_frame, text="Clear", command=self.clear_files).pack(pady=5)
        tk.Button(control_frame, text="Plot", command=self.plot_files).pack(pady=5)

        tk.Checkbutton(control_frame, text="Log X", variable=self.log_x, command=self.plot_files).pack(anchor="w")
        tk.Checkbutton(control_frame, text="Log Y", variable=self.log_y, command=self.plot_files).pack(anchor="w")

        tk.Label(control_frame, text="Filename:").pack(pady=(10, 0))
        self.filename_entry = tk.Entry(control_frame)
        self.filename_entry.pack(fill="x")
        self.filename_entry.insert(0, "plot.png")

        tk.Button(control_frame, text="Save Plot", command=self.save_plot).pack(pady=5)

        tk.Label(control_frame, text="Plot Title (LaTeX):").pack(pady=(10, 0))
        self.title_entry = tk.Entry(control_frame)
        self.title_entry.pack(fill="x")
        self.title_entry.bind("<KeyRelease>", lambda event: self.plot_files())

        header = tk.Frame(control_frame)
        header.pack()
        for text, width in zip(["Folder", "File", "Method", "Deg", "Xmin", "Xmax", "Legend"], [12, 15, 8, 4, 6, 6, 20]):
            tk.Label(header, text=text, width=width).pack(side="left")

        self.file_frame = tk.Frame(control_frame)
        self.file_frame.pack(fill="both", expand=True, pady=(5, 0))

# === 3. File management ===
    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt")])
        for path in paths:
            if not any(f.filepath == path for f in self.files):
                entry = FileEntry(path)
                try:
                    df = pd.read_csv(path, delim_whitespace=True, header=None)
                    df.columns = ['Mass', 'CrossSection']
                    x = df['Mass'].values
                    entry.data_min = np.min(x)
                    entry.data_max = np.max(x)
                    entry.xmin.set(str(entry.data_min))
                    entry.xmax.set(str(entry.data_max))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read {path}:\n{e}")
                    continue

                self.files.append(entry)
                self.add_file_widget(entry)
        self.plot_files()

    def add_file_widget(self, entry):
        row = tk.Frame(self.file_frame)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=entry.subdir, width=12, anchor="w").pack(side="left")
        tk.Label(row, text=entry.label, width=15, anchor="w").pack(side="left")
        tk.OptionMenu(row, entry.method, "None", "LOWESS", "PCHIP", "Spline", "PolyFit", command=lambda *_: self.update_method(entry)).pack(side="left")

        deg_entry = tk.Entry(row, textvariable=entry.poly_degree, width=4)
        deg_entry.pack(side="left")
        deg_entry.bind("<KeyRelease>", lambda event: self.plot_files())

        entry._xmin_widget = tk.Entry(row, textvariable=entry.xmin, width=6)
        entry._xmax_widget = tk.Entry(row, textvariable=entry.xmax, width=6)
        entry._xmin_widget.pack(side="left")
        entry._xmax_widget.pack(side="left")
        entry._xmin_widget.bind("<KeyRelease>", lambda e: self.plot_files())
        entry._xmax_widget.bind("<KeyRelease>", lambda e: self.plot_files())

        legend = tk.Entry(row, textvariable=entry.custom_label, width=25)
        legend.pack(side="left", padx=5)
        legend.bind("<KeyRelease>", lambda e: self.plot_files())

        self.update_method(entry)

    def update_method(self, entry):
        method = entry.method.get()
        state = "normal" if method != "None" else "disabled"
        entry._xmin_widget.config(state=state)
        entry._xmax_widget.config(state=state)

        if method == "None":
            entry.xmin.set(str(entry.data_min))
            entry.xmax.set(str(entry.data_max))

        self.plot_files()

    def clear_files(self):
        self.files.clear()
        for w in self.file_frame.winfo_children():
            w.destroy()
        self.plot_files()

# === 4. Plotting ===
    def plot_files(self):
        self.ax.clear()
        all_y = []

        for entry in self.files:
            try:
                df = pd.read_csv(entry.filepath, delim_whitespace=True, header=None)
                df.columns = ['Mass', 'CrossSection']
                x, y = df['Mass'].values, df['CrossSection'].values

                try:
                    xmin, xmax = float(entry.xmin.get()), float(entry.xmax.get())
                except ValueError:
                    xmin, xmax = x.min(), x.max()

                mask = (x >= xmin) & (x <= xmax)
                x_use, y_use = x[mask], y[mask]
                x_full = np.linspace(xmin, xmax, 1000)

                method = entry.method.get()
                label = entry.custom_label.get().strip() or None

                if method == "LOWESS":
                    x_s, y_s = lowess(y_use, x_use, frac=0.15, return_sorted=True).T
                    y_interp = np.interp(x_full, x_s, y_s)
                    y_plot = y_interp
                    self.ax.plot(x_full, y_plot, label=label, linewidth=3)

                elif method == "PCHIP":
                    interp = PchipInterpolator(x_use, y_use, extrapolate=False)
                    y_plot = interp(x_full)
                    self.ax.plot(x_full, y_plot, label=label, linewidth=3)

                elif method == "Spline":
                    spline = UnivariateSpline(x_use, y_use, s=0.5)
                    y_plot = spline(x_full)
                    self.ax.plot(x_full, y_plot, label=label, linewidth=3)

                elif method == "PolyFit":
                    deg = int(entry.poly_degree.get()) if entry.poly_degree.get().isdigit() else 5
                    coeffs = np.polyfit(x_use, y_use, deg=deg)
                    poly = np.poly1d(coeffs)
                    y_plot = poly(x_full)
                    self.ax.plot(x_full, y_plot, label=label, linewidth=3)

                else:
                    self.ax.plot(x_use, y_use, label=label, linewidth=3)
                    y_plot = y_use

                all_y.extend(y_plot[np.isfinite(y_plot)])

            except Exception as e:
                messagebox.showerror("Plot Error", f"{entry.label}:\n{e}")

        title = self.title_entry.get().strip()
        if title:
            self.ax.set_title(title, fontsize=22)

        self.ax.set_xlabel(r"$M_{\phi_b}$ [GeV]", fontsize=20)
        self.ax.set_ylabel(r"$\sigma$ [pb]", fontsize=20)
        self.ax.set_xscale('log' if self.log_x.get() else 'linear')
        self.ax.set_yscale('log' if self.log_y.get() else 'linear')

        if all_y and not self.log_y.get():
            ymin, ymax = min(all_y), max(all_y)
            if ymin == ymax:
                ymin *= 0.9
                ymax *= 1.1
            self.ax.set_ylim(ymin, ymax)

        formatter = FuncFormatter(lambda x, _: f"$10^{{{int(np.log10(x))}}}$" if x > 0 else "$0$")
        self.ax.yaxis.set_major_formatter(formatter)

        self.ax.grid(True, which="both", linestyle=":", linewidth=0.7)
        self.ax.minorticks_on()
        self.ax.tick_params(axis="both", labelsize=15)

        if any(f.custom_label.get().strip() for f in self.files):
            self.ax.legend(fontsize=18)

        self.canvas.draw()
 
# === 5. Saving ===
    def save_plot(self):
        filename = self.filename_entry.get().strip()
        if not filename.endswith(".png"):
            filename += ".png"
        try:
            self.fig.savefig(filename, dpi=300)
            messagebox.showinfo("Saved", f"Plot saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

# === 6. Run application ===
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1800x900")
    app = IndividualPlotApp(root)
    root.mainloop()
