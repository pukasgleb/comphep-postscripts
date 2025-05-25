import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt
import os
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib.ticker import ScalarFormatter
import numpy as np
import shutil

class MultiGraphApp:
# === 1. Initialization ===
    def __init__(self, root):
        self.root = root
        self.root.title("Cross Section Graph Viewer")

        self.process_type = tk.StringVar(value="weak t-channel process")
        self.energy_choice = tk.StringVar(value="14")
        self.final_state_choice = tk.StringVar(value="2X")
        self.sum_mode = tk.BooleanVar()

        self.selected_folder = tk.StringVar()
        self.available_graphs = {}

        self.log_x = tk.BooleanVar()
        self.log_y = tk.BooleanVar()
        self.trend_only = tk.BooleanVar()
        self.frac = tk.DoubleVar(value=0.15)
        self.x_min = tk.DoubleVar()
        self.x_max = tk.DoubleVar()
        self.fix_x_min = tk.BooleanVar()
        self.fix_x_max = tk.BooleanVar()
        self.edit_mode = tk.BooleanVar()

        self.selected_final_states = {
            "2X": tk.BooleanVar(value=True),
            "3X": tk.BooleanVar(value=True),
            "4X": tk.BooleanVar(value=True)
        }

        self.last_selected_folder = None
        self.dragging_point = None
        self.active_line_data = {}

        self.build_interface()

# === 2. GUI Layout ===
    def build_interface(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, width=250)
        left.pack(side="left", fill="y", padx=5, pady=5)
        middle = tk.Frame(main, width=250)
        middle.pack(side="left", fill="y", padx=5, pady=5)
        right = tk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        # Process type
        tk.Label(left, text="Process Type:").pack(anchor="w")
        for label in ["weak t-channel process", "associated production", "pair production"]:
            tk.Radiobutton(left, text=label, variable=self.process_type, value=label, command=self.refresh_folders).pack(anchor="w")

        # Energy
        tk.Label(left, text="Energy (TeV):").pack(anchor="w", pady=(10, 0))
        for val in ["14", "100"]:
            tk.Radiobutton(left, text=val, variable=self.energy_choice, value=val, command=self.refresh_folders).pack(anchor="w")

        tk.Checkbutton(left, text="Summation Mode", variable=self.sum_mode, command=self.toggle_sum_mode).pack(anchor="w", pady=(10, 0))

        # Final state selection
        self.final_state_frame = tk.Frame(left)
        self.final_state_frame.pack(anchor="w", pady=(5, 0))

        self.final_state_radiobuttons = []
        self.final_state_checkbuttons = []

        for val in ["2X", "3X", "4X"]:
            rb = tk.Radiobutton(self.final_state_frame, text=val, variable=self.final_state_choice, value=val, command=self.refresh_folders)
            cb = tk.Checkbutton(self.final_state_frame, text=val, variable=self.selected_final_states[val], command=self.refresh_folders)
            self.final_state_radiobuttons.append(rb)
            self.final_state_checkbuttons.append(cb)
            rb.pack(anchor="w")

        # Axis controls
        tk.Checkbutton(left, text="Logarithmic X", variable=self.log_x, command=self.update_plot).pack(anchor="w", pady=(10, 0))
        tk.Checkbutton(left, text="Logarithmic Y", variable=self.log_y, command=self.update_plot).pack(anchor="w")
        tk.Checkbutton(left, text="Show LOWESS Only", variable=self.trend_only, command=self.update_plot).pack(anchor="w")

        tk.Checkbutton(left, text="Point Edit Mode", variable=self.edit_mode, command=self.update_plot).pack(anchor="w", pady=(10, 0))

        # LOWESS
        tk.Label(left, text="LOWESS frac:").pack(anchor="w", pady=(10, 0))
        tk.Scale(left, from_=0.05, to=0.5, resolution=0.01, orient=tk.HORIZONTAL, variable=self.frac, command=lambda val: self.update_plot()).pack(fill="x")

        # X range
        range_frame = tk.Frame(left)
        range_frame.pack(anchor="w", pady=(10, 0))

        tk.Label(range_frame, text="X min:").grid(row=0, column=0)
        entry_xmin = tk.Entry(range_frame, textvariable=self.x_min, width=8)
        entry_xmin.grid(row=0, column=1)
        tk.Checkbutton(range_frame, variable=self.fix_x_min, command=self.update_plot).grid(row=0, column=2)

        tk.Label(range_frame, text="X max:").grid(row=1, column=0)
        entry_xmax = tk.Entry(range_frame, textvariable=self.x_max, width=8)
        entry_xmax.grid(row=1, column=1)
        tk.Checkbutton(range_frame, variable=self.fix_x_max, command=self.update_plot).grid(row=1, column=2)

        entry_xmin.bind("<Return>", lambda event: self.update_plot())
        entry_xmin.bind("<FocusOut>", lambda event: self.update_plot())
        entry_xmax.bind("<Return>", lambda event: self.update_plot())
        entry_xmax.bind("<FocusOut>", lambda event: self.update_plot())

        tk.Button(left, text="Reset X Range", command=self.reset_mass_range).pack(pady=5)
        tk.Button(left, text="Save Plot", command=self.save_plot).pack(pady=5)

        # Folder and graph selectors
        folders_frame = tk.LabelFrame(middle, text="Calculation Folders")
        folders_frame.pack(fill="x")
        self.folders_panel = tk.Frame(folders_frame)
        self.folders_panel.pack()

        graphs_frame = tk.LabelFrame(middle, text="Graphs")
        graphs_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.graphs_panel = tk.Frame(graphs_frame)
        self.graphs_panel.pack()

        # Plot display
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)

        self.refresh_folders()

# === 3. Folder and file logic ===
    def toggle_sum_mode(self):
        if self.sum_mode.get():
            for rb in self.final_state_radiobuttons:
                rb.pack_forget()
            for cb in self.final_state_checkbuttons:
                cb.pack(anchor="w")
        else:
            for cb in self.final_state_checkbuttons:
                cb.pack_forget()
            for rb in self.final_state_radiobuttons:
                rb.pack(anchor="w")
        self.refresh_folders()

    def build_base_path(self, final_state=None):
        final_state = final_state or self.final_state_choice.get()
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.process_type.get(),
            self.energy_choice.get(),
            final_state
        )

    def refresh_folders(self):
        for widget in self.folders_panel.winfo_children():
            widget.destroy()

        folders = set()
        if self.sum_mode.get():
            for final_state, var in self.selected_final_states.items():
                if var.get():
                    base_path = self.build_base_path(final_state)
                    if os.path.exists(base_path):
                        folders.update(d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)))
        else:
            base_path = self.build_base_path()
            if os.path.exists(base_path):
                folders = set(d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)))

        folders = sorted(folders)
        if self.last_selected_folder not in folders:
            self.selected_folder.set(folders[0] if folders else "")
        else:
            self.selected_folder.set(self.last_selected_folder)

        for folder in folders:
            tk.Radiobutton(self.folders_panel, text=folder, variable=self.selected_folder, value=folder, command=self.load_graphs_from_folder).pack(anchor="w")

        self.load_graphs_from_folder()

    def collect_files(self):
        result = {}
        if self.sum_mode.get():
            for final_state, var in self.selected_final_states.items():
                if var.get():
                    folder_path = os.path.join(self.build_base_path(final_state), self.selected_folder.get())
                    if os.path.exists(folder_path):
                        for file in os.listdir(folder_path):
                            if file.endswith(".txt"):
                                result[(final_state, file)] = os.path.join(folder_path, file)
        else:
            folder_path = os.path.join(self.build_base_path(), self.selected_folder.get())
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith(".txt"):
                        result[(self.final_state_choice.get(), file)] = os.path.join(folder_path, file)
        return result

    def load_graphs_from_folder(self):
        self.last_selected_folder = self.selected_folder.get()
        for widget in self.graphs_panel.winfo_children():
            widget.destroy()
        self.available_graphs.clear()

        paths = self.collect_files()
        for (final_state, filename) in sorted(paths.keys()):
            var = tk.BooleanVar(value=True)
            self.available_graphs[filename] = var
            tk.Checkbutton(self.graphs_panel, text=filename.replace(".txt", ""), variable=var, command=self.update_plot).pack(anchor="w")

        self.auto_set_mass_range()
        self.update_plot()

    def auto_set_mass_range(self):
        all_masses = []
        paths = self.collect_files()
        for (final_state, filename), path in paths.items():
            if self.available_graphs.get(filename, tk.BooleanVar(value=True)).get():
                try:
                    df = pd.read_csv(path, delim_whitespace=True, header=None)
                    df.columns = ['Mass', 'CrossSection']
                    all_masses.extend(df['Mass'].values)
                except:
                    continue
        if all_masses:
            if not self.fix_x_min.get():
                self.x_min.set(min(all_masses))
            if not self.fix_x_max.get():
                self.x_max.set(max(all_masses))

    def beautify_filename(self, filename):
        name = filename.replace(".txt", "")
        latex_names = {
            "phi": r"\phi", "phia": r"\phi_{a}", "phib": r"\phi_{b}",
            "phia_conj": r"\phi_{a}^{*}", "phib_conj": r"\phi_{b}^{*}",
            "psi": r"\psi", "psia": r"\psi_{a}", "psib": r"\psi_{b}",
            "psia_conj": r"\psi_{a}^{*}", "psib_conj": r"\psi_{b}^{*}",
        }
        latex_parts = [latex_names.get(part, part) for part in name.split("_")]
        return r"$" + r" \, ".join(latex_parts) + r"$"

# === 4. Plotting ===
    def update_plot(self, *_):
        self.ax.clear()
        self.active_line_data.clear()

        folder_paths = self.collect_files()
        data = []

        for (final_state, filename), path in folder_paths.items():
            if not self.available_graphs.get(filename, tk.BooleanVar(value=True)).get():
                continue
            try:
                df = pd.read_csv(path, delim_whitespace=True, header=None)
                df.columns = ['Mass', 'CrossSection']
                data.append((final_state, filename, df, path))
            except:
                continue

        if not data:
            self.canvas.draw()
            return

        x_min = self.x_min.get() if self.fix_x_min.get() else None
        x_max = self.x_max.get() if self.fix_x_max.get() else None

        if self.sum_mode.get():
            masses = sorted(set(np.concatenate([df['Mass'].values for (_, _, df, _) in data])))
            sum_y = np.zeros_like(masses, dtype=float)

            for (_, _, df, _) in data:
                interp_y = np.interp(masses, df['Mass'].values, df['CrossSection'].values)
                sum_y += interp_y

            x, y = np.array(masses), sum_y
            mask = np.ones_like(x, dtype=bool)
            if x_min is not None: mask &= (x >= x_min)
            if x_max is not None: mask &= (x <= x_max)

            x, y = x[mask], y[mask]
            if self.trend_only.get():
                x_s, y_s = lowess(y, x, frac=self.frac.get(), return_sorted=True).T
                self.ax.plot(x_s, y_s, label="Total Cross Section")
            else:
                self.ax.plot(x, y, marker='o', linestyle='-', label="Total Cross Section")

        else:
            for (final_state, filename, df, path) in data:
                x = df['Mass'].values
                y = df['CrossSection'].values

                mask = np.ones_like(x, dtype=bool)
                if x_min is not None: mask &= (x >= x_min)
                if x_max is not None: mask &= (x <= x_max)

                x_plot, y_plot = x[mask], y[mask]
                label = self.beautify_filename(filename)

                if self.trend_only.get():
                    x_s, y_s = lowess(y_plot, x_plot, frac=self.frac.get(), return_sorted=True).T
                    line, = self.ax.plot(x_s, y_s, label=label)
                else:
                    line, = self.ax.plot(x_plot, y_plot, marker='o', linestyle='-', label=label)

                if self.edit_mode.get():
                    self.active_line_data[line] = {
                        'filename': filename,
                        'final_state': final_state,
                        'df': df,
                        'path': path
                    }

        folder = self.selected_folder.get()
        try:
            mr, sin_theta, lam = folder.split("_")
            title = fr"$\sqrt{{s}} = {self.energy_choice.get()}$ TeV, $M_r = {mr}$ GeV, $\sin\theta = {sin_theta}$, $\Lambda = {lam}$ GeV"
        except ValueError:
            title = folder

        self.ax.set_title(title, fontsize=22)
        self.ax.set_xlabel(r"$M_{\phi_b}$ [GeV]", fontsize=18)
        self.ax.set_ylabel(r"$\sigma_\mathrm{process}$ [pb]", fontsize=18)
        self.ax.grid(True)

        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((0, 0))
        self.ax.yaxis.set_major_formatter(formatter)

        self.ax.set_xscale('log' if self.log_x.get() else 'linear')
        self.ax.set_yscale('log' if self.log_y.get() else 'linear')
        self.ax.legend(fontsize=13)
        self.canvas.draw()

# === 5. Point Editing ===
    def on_press(self, event):
        if not self.edit_mode.get() or event.inaxes != self.ax:
            return
        for line, info in self.active_line_data.items():
            contains, attr = line.contains(event)
            if contains:
                ind = attr['ind'][0]
                self.dragging_point = (line, ind)
                return

    def on_motion(self, event):
        if not self.dragging_point or not self.edit_mode.get() or event.inaxes != self.ax:
            return
        line, idx = self.dragging_point
        xdata, ydata = list(line.get_xdata()), list(line.get_ydata())
        ydata[idx] = event.ydata
        line.set_data(xdata, ydata)
        self.canvas.draw()

    def on_release(self, event):
        if not self.dragging_point or not self.edit_mode.get():
            return
        line, idx = self.dragging_point
        info = self.active_line_data.get(line)
        if info:
            df = info['df']
            path = info['path']
            x_mass = df.iloc[idx, 0]
            new_value = event.ydata
            closest_idx = (df['Mass'] - x_mass).abs().idxmin()
            df.at[closest_idx, 'CrossSection'] = new_value
            backup_path = path + ".bak"
            if not os.path.exists(backup_path):
                shutil.copy2(path, backup_path)
            df.to_csv(path, sep=' ', header=False, index=False)
        self.dragging_point = None

# === 6. Utilities ===
    def reset_mass_range(self):
        self.fix_x_min.set(False)
        self.fix_x_max.set(False)
        self.auto_set_mass_range()
        self.update_plot()

    def save_plot(self):
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_graphs")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{self.selected_folder.get()}_plot.png"
        self.fig.savefig(os.path.join(save_dir, filename), dpi=300)
        messagebox.showinfo("Saved", f"Plot saved to:\n{save_dir}")

# === 7. Run Application ===
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1800x950")
    app = MultiGraphApp(root)
    root.mainloop()
