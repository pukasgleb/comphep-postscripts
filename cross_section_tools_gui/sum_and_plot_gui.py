import os
import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.interpolate import PchipInterpolator, UnivariateSpline
from matplotlib.ticker import FuncFormatter
import shutil

class EditableSumApp:
# === 1. Initialization ===
    def __init__(self, root):
        self.root = root
        self.root.title("Summation, Smoothing, and Graph Editing")

        self.last_save_dir = None
        self.process_type = tk.StringVar(value="weak t-channel process")
        self.energy_choice = tk.StringVar(value="14")

        self.selected_folders = {}
        self.smoothing_methods = {}

        self.log_x = tk.BooleanVar()
        self.log_y = tk.BooleanVar()
        self.edit_mode = tk.BooleanVar()
        self.frac = tk.DoubleVar(value=0.15)

        self.x_min = tk.DoubleVar()
        self.x_max = tk.DoubleVar()
        self.fix_x_min = tk.BooleanVar()
        self.fix_x_max = tk.BooleanVar()

        self.dragging_point = None
        self.editable_lines = {}

        self.build_interface()

# === 2. Interface ===
    def build_interface(self):
        left_panel = tk.Frame(self.root)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)

        tk.Label(left_panel, text="Process Type:").pack(anchor="w")
        for label in ["weak t-channel process", "associated production", "pair production"]:
            tk.Radiobutton(left_panel, text=label, variable=self.process_type, value=label, command=self.refresh_folders).pack(anchor="w")

        tk.Label(left_panel, text="Energy (TeV):").pack(anchor="w", pady=(10, 0))
        for val in ["14", "100"]:
            tk.Radiobutton(left_panel, text=val, variable=self.energy_choice, value=val, command=self.refresh_folders).pack(anchor="w")

        self.folder_list_panel = tk.LabelFrame(left_panel, text="Parameter Sets")
        self.folder_list_panel.pack(fill="both", expand=True, pady=(10, 0))

        tk.Checkbutton(left_panel, text="Logarithmic X", variable=self.log_x, command=self.update_plot).pack(anchor="w")
        tk.Checkbutton(left_panel, text="Logarithmic Y", variable=self.log_y, command=self.update_plot).pack(anchor="w")
        tk.Checkbutton(left_panel, text="Edit Mode", variable=self.edit_mode, command=self.update_plot).pack(anchor="w", pady=(10, 0))

        tk.Label(left_panel, text="LOWESS frac:").pack(anchor="w", pady=(10, 0))
        tk.Scale(left_panel, from_=0.05, to=0.5, resolution=0.01, orient=tk.HORIZONTAL, variable=self.frac, command=lambda _: self.update_plot()).pack(fill="x")

        range_frame = tk.Frame(left_panel)
        range_frame.pack(anchor="w", pady=(10, 0))

        tk.Label(range_frame, text="X min:").grid(row=0, column=0)
        tk.Entry(range_frame, textvariable=self.x_min, width=8).grid(row=0, column=1)
        tk.Checkbutton(range_frame, variable=self.fix_x_min, command=self.update_plot).grid(row=0, column=2)

        tk.Label(range_frame, text="X max:").grid(row=1, column=0)
        tk.Entry(range_frame, textvariable=self.x_max, width=8).grid(row=1, column=1)
        tk.Checkbutton(range_frame, variable=self.fix_x_max, command=self.update_plot).grid(row=1, column=2)

        tk.Label(left_panel, text="Filename:").pack(anchor="w", pady=(10, 0))
        self.filename_entry = tk.Entry(left_panel)
        self.filename_entry.pack(fill="x")
        tk.Button(left_panel, text="Save Plot", command=self.save_plot_dialog).pack(pady=(5, 10))

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)

        self.refresh_folders()

# === 3. Logic ===
    def get_base_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.process_type.get(), self.energy_choice.get())

    def refresh_folders(self):
        for widget in self.folder_list_panel.winfo_children():
            widget.destroy()
        base_path = self.get_base_path()
        names = set()

        for state in ['2X', '3X', '4X']:
            path = os.path.join(base_path, state)
            if os.path.exists(path):
                for name in os.listdir(path):
                    if os.path.isdir(os.path.join(path, name)):
                        names.add(name)

        self.selected_folders.clear()
        self.smoothing_methods.clear()
        for name in sorted(names):
            frame = tk.Frame(self.folder_list_panel)
            frame.pack(anchor="w", fill="x")
            var = tk.BooleanVar()
            self.selected_folders[name] = var
            smooth_var = tk.StringVar(value="None")
            self.smoothing_methods[name] = smooth_var
            tk.Checkbutton(frame, text=name, variable=var, command=self.update_plot).pack(side="left")
            tk.OptionMenu(frame, smooth_var, "None", "LOWESS", "PCHIP", "Spline", "PolyFit", command=lambda _: self.update_plot()).pack(side="left")

        self.update_plot()

    def collect_data(self, folder):
        dfs = []
        for state in ['2X', '3X', '4X']:
            path = os.path.join(self.get_base_path(), state, folder)
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(".txt"):
                        try:
                            df = pd.read_csv(os.path.join(path, file), delim_whitespace=True, header=None)
                            df.columns = ['Mass', 'CrossSection']
                            dfs.append(df)
                        except:
                            continue
        return dfs

    def get_sum_path(self, folder):
        return os.path.join(self.get_base_path(), "Sum", f"{folder}.txt")

    def save_sum_file(self, folder, x, y):
        path = self.get_sum_path(folder)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df = pd.DataFrame({'Mass': x, 'CrossSection': y})
        df.to_csv(path, sep=' ', header=False, index=False)

# === 4. Plotting ===
    def update_plot(self):
        self.ax.clear()
        self.editable_lines.clear()
        selected = [name for name, var in self.selected_folders.items() if var.get()]
        if not selected:
            self.canvas.draw()
            return

        for name in selected:
            sum_path = self.get_sum_path(name)
            if os.path.exists(sum_path):
                df = pd.read_csv(sum_path, delim_whitespace=True, header=None)
                df.columns = ['Mass', 'CrossSection']
            else:
                dfs = self.collect_data(name)
                if not dfs:
                    continue
                all_masses = np.concatenate([df['Mass'].values for df in dfs])
                x_min, x_max = np.min(all_masses), np.max(all_masses)
                if self.fix_x_min.get(): x_min = self.x_min.get()
                if self.fix_x_max.get(): x_max = self.x_max.get()
                x = np.linspace(x_min, x_max, 300)
                y = np.zeros_like(x)
                for df in dfs:
                    y_interp = np.interp(x, df['Mass'], df['CrossSection'], left=0, right=0)
                    y += y_interp
                df = pd.DataFrame({'Mass': x, 'CrossSection': y})
                self.save_sum_file(name, x, y)

            x = df['Mass'].values
            y = df['CrossSection'].values + 1e-10  # avoid log(0)
            if self.fix_x_min.get(): mask = x >= self.x_min.get(); x, y = x[mask], y[mask]
            if self.fix_x_max.get(): mask = x <= self.x_max.get(); x, y = x[mask], y[mask]

            method = self.smoothing_methods.get(name, tk.StringVar(value="None")).get()
            label = name
            if method == "LOWESS":
                x_s, y_s = lowess(y, x, frac=self.frac.get(), return_sorted=True).T
                self.ax.plot(x_s, y_s, label=label, linewidth=3)
            elif method == "PCHIP":
                interp = PchipInterpolator(x, y)
                x_s = np.linspace(x.min(), x.max(), 1000)
                y_s = interp(x_s)
                self.ax.plot(x_s, y_s, label=label, linewidth=3)
            elif method == "Spline":
                spline = UnivariateSpline(x, y, s=0.5)
                x_s = np.linspace(x.min(), x.max(), 1000)
                self.ax.plot(x_s, spline(x_s), label=label, linewidth=3)
            elif method == "PolyFit":
                coeffs = np.polyfit(x, y, deg=5)
                poly = np.poly1d(coeffs)
                x_s = np.linspace(x.min(), x.max(), 1000)
                self.ax.plot(x_s, poly(x_s), label=label, linewidth=3)
            else:
                line, = self.ax.plot(x, y, label=label, linewidth=3)
                if self.edit_mode.get():
                    self.editable_lines[line] = {'df': df, 'path': self.get_sum_path(name)}

        self.ax.set_title(
            rf"{self.process_type.get()} $\sqrt{{s}} = {self.energy_choice.get()}$ TeV",
            fontsize=20
            )
        self.ax.set_xlabel("Mass [GeV]", fontsize=18)
        self.ax.set_ylabel("Cross Section [pb]", fontsize=18)
        self.ax.set_xscale('log' if self.log_x.get() else 'linear')
        self.ax.set_yscale('log' if self.log_y.get() else 'linear')
        self.ax.grid(True, which='both', linestyle=':', linewidth=0.7)
        self.ax.legend()
        self.canvas.draw()

# === 5. Editing ===
    def on_press(self, event):
        if not self.edit_mode.get() or event.inaxes != self.ax:
            return
        for line, info in self.editable_lines.items():
            contains, attr = line.contains(event)
            if contains:
                self.dragging_point = (line, attr['ind'][0])
                return

    def on_motion(self, event):
        if not self.dragging_point or not self.edit_mode.get() or event.inaxes != self.ax:
            return
        line, idx = self.dragging_point
        xdata, ydata = list(line.get_xdata()), list(line.get_ydata())
        ydata[idx] = max(event.ydata, 1e-10)
        line.set_data(xdata, ydata)
        self.canvas.draw()

    def on_release(self, event):
        if not self.dragging_point: return
        line, idx = self.dragging_point
        info = self.editable_lines[line]
        df, path = info['df'], info['path']
        x_mass = df.iloc[idx, 0]
        new_val = max(event.ydata, 1e-10)
        nearest_idx = (df['Mass'] - x_mass).abs().idxmin()
        df.at[nearest_idx, 'CrossSection'] = new_val
        backup = path + ".bak"
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
        df.to_csv(path, sep=' ', header=False, index=False)
        self.dragging_point = None

# === 6. Save ===
    def save_plot_dialog(self):
        if not self.last_save_dir:
            directory = filedialog.askdirectory()
            if not directory:
                return
            self.last_save_dir = directory
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Filename cannot be empty.")
            return
        if not filename.endswith(".png"):
            filename += ".png"
        try:
            self.fig.savefig(os.path.join(self.last_save_dir, filename), dpi=300)
            messagebox.showinfo("Saved", "Plot saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# === 7. Run ===
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1800x950")
    app = EditableSumApp(root)
    root.mainloop()