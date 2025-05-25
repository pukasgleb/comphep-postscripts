import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FileMoverApp:

# === 1. Initialization ===
    def __init__(self, root):
        self.root = root
        self.root.title("File Renaming and Transfer Tool")

        self.choice_var = tk.StringVar(value="2X")
        self.m_r_var = tk.StringVar()
        self.sin_theta_var = tk.StringVar()
        self.lambda_var = tk.StringVar()

        self.files_to_rename = {}
        self.folder_target_vars = {}
        self.file_entries = {}

        self.start_folder = os.getcwd()

        self.final_processes = [
            "weak t-channel process",
            "associated production",
            "pair production"
        ]
        self.energies = ["14", "100"]

        self.default_mapping = {
            "comphep_1": ("weak t-channel process", "14"),
            "comphep_2": ("weak t-channel process", "100"),
            "comphep_3": ("associated production", "14"),
            "comphep_4": ("associated production", "100"),
            "comphep_5": ("pair production", "14"),
            "comphep_6": ("pair production", "100"),
            "comphep": ("weak t-channel process", "14"),
        }

        self.rename_map = {
            "cb": "phib", "Cb": "phib_conj",
            "ca": "phia", "Ca": "phia_conj",
            "ch": "phi",
            "ha": "psia", "Ha": "psia_conj",
            "hb": "psib", "Hb": "psib_conj"
        }

        self.default_suffixes = {
            "2X": [["cb", "Cb"], ["ca", "Ca"], ["ch", "ch"], ["hb", "Hb"], ["ha", "Ha"]],
            "3X": [["Cb", "Cb", "Cb"], ["Ca", "Cb", "Cb"], ["ch", "cb", "Cb"], ["Ca", "Ca", "Cb"],
                   ["Ha", "hb", "Cb"], ["cb", "cb", "cb"], ["ca", "cb", "cb"], ["ca", "ca", "cb"],
                   ["ha", "Hb", "cb"], ["Ca", "Ca", "Ca"], ["ch", "ca", "Ca"], ["Ha", "hb", "Ca"],
                   ["ca", "ca", "ca"], ["ha", "Hb", "ca"], ["ch", "ch", "ch"], ["hb", "Hb", "ch"],
                   ["ha", "Ha", "ch"]],
            "4X": [["ch", "Cb", "Cb", "Cb"], ["cb", "cb", "Cb", "Cb"], ["ch", "Ca", "Cb", "Cb"],
                   ["ca", "ca", "Cb", "Cb"], ["ca", "Ca", "cb", "Cb"], ["ch", "ch", "cb", "Cb"],
                   ["ch", "Ca", "Ca", "Cb"], ["ch", "cb", "cb", "cb"], ["Ca", "Ca", "cb", "cb"],
                   ["ch", "ca", "cb", "cb"], ["ch", "ca", "ca", "cb"], ["ch", "Ca", "Ca", "Ca"],
                   ["ca", "ca", "Ca", "Ca"], ["ch", "ch", "ca", "Ca"], ["ch", "ca", "ca", "ca"],
                   ["ch", "ch", "ch", "ch"]]
        }

        self.build_gui()
        root.after(100, self.find_files)

# === 2. Build GUI layout ===
    def build_gui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="y")

        top_frame = tk.Frame(left_frame)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="Mode:").grid(row=0, column=0, sticky="w")
        radio_frame = tk.Frame(top_frame)
        radio_frame.grid(row=0, column=1, columnspan=5, sticky="w", padx=10)
        for i, opt in enumerate(["2X", "3X", "4X"]):
            tk.Radiobutton(radio_frame, text=opt, variable=self.choice_var, value=opt).grid(row=0, column=i, padx=10)

        tk.Label(top_frame, text="M_r:").grid(row=1, column=0, sticky="e")
        tk.Entry(top_frame, textvariable=self.m_r_var).grid(row=1, column=1, sticky="w")
        tk.Label(top_frame, text="Lambda:").grid(row=1, column=2, sticky="e")
        tk.Entry(top_frame, textvariable=self.lambda_var).grid(row=1, column=3, sticky="w")
        tk.Label(top_frame, text="sin θ:").grid(row=1, column=4, sticky="e")
        tk.Entry(top_frame, textvariable=self.sin_theta_var).grid(row=1, column=5, sticky="w")

        tk.Button(top_frame, text="Choose Start Folder", command=self.choose_folder).grid(row=2, column=0, columnspan=2, pady=5, sticky="w")
        tk.Button(top_frame, text="Find Files", command=self.find_files).grid(row=2, column=2, columnspan=2, pady=5, sticky="w")

        self.mapping_frame = tk.Frame(left_frame)
        self.mapping_frame.pack(pady=10, fill="x")

        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        self.copy_button = tk.Button(left_frame, text="Copy from First Tab to All", command=self.copy_from_first_tab, state="disabled")
        self.copy_button.pack(pady=5)

        self.move_button = tk.Button(left_frame, text="Transfer Files", command=self.move_files, state="disabled")
        self.move_button.pack(pady=10)

        tk.Label(right_frame, text="Action Log:").pack()
        self.log_text = tk.Text(right_frame, width=50, height=40, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

# === 3. Folder Selection and file discovery ===
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select folder with comphep_*")
        if folder:
            self.start_folder = folder
            messagebox.showinfo("Folder Selected", f"Selected path:\n{folder}")
            self.find_files()

    def append_log(self, line):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, line + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)

    def find_files(self):
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.files_to_rename.clear()
        self.folder_target_vars.clear()
        self.file_entries.clear()

        if not self.validate_start_folder():
            return

        row = 0
        for folder in sorted(os.listdir(self.start_folder)):
            folder_path = os.path.join(self.start_folder, folder)
            is_comphep_star = folder.startswith("comphep_")
            is_comphep = folder.lower() == "comphep"

            if os.path.isdir(folder_path) and (is_comphep_star or is_comphep):
                results_path = os.path.join(folder_path, "results")
                files = []
                if os.path.exists(results_path):
                    hist_files = [f for f in os.listdir(results_path)
                                  if f.startswith("hist1d_") and f.endswith(".txt")]
                    hist_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
                    files = [os.path.join(results_path, f) for f in hist_files]

                self.files_to_rename[folder] = files

                selected_var = tk.BooleanVar(value=not is_comphep)
                process_var = tk.StringVar()
                energy_var = tk.StringVar()
                process_var.set(self.default_mapping.get(folder, ("", ""))[0])
                energy_var.set(self.default_mapping.get(folder, ("", ""))[1])

                tk.Checkbutton(self.mapping_frame, text=folder, variable=selected_var,
                               command=lambda f=folder: self.toggle_tab(f)).grid(row=row, column=0, sticky="w")
                ttk.Combobox(self.mapping_frame, textvariable=process_var, values=self.final_processes, width=30).grid(row=row, column=1)
                ttk.Combobox(self.mapping_frame, textvariable=energy_var, values=self.energies, width=5).grid(row=row, column=2)

                self.folder_target_vars[folder] = {
                    "selected": selected_var,
                    "process": process_var,
                    "energy": energy_var
                }

                tab = tk.Frame(self.notebook)
                self.notebook.add(tab, text=folder)
                self.notebook.tab(tab, state="normal" if selected_var.get() else "disabled")

                file_entries = []
                options = self.get_default_options()
                if files:
                    for idx, file_path in enumerate(files):
                        tk.Label(tab, text=os.path.basename(file_path)).grid(row=idx, column=0, sticky="w")
                        combo = ttk.Combobox(tab, values=options, width=40)
                        combo.grid(row=idx, column=1)
                        if idx < len(options):
                            combo.set(options[idx])
                        file_entries.append(combo)
                else:
                    tk.Label(tab, text="No files to display").grid(row=0, column=0, sticky="w")

                self.file_entries[folder] = file_entries
                row += 1

        if self.files_to_rename:
            self.move_button.config(state="normal")
            self.copy_button.config(state="normal")
        else:
            messagebox.showinfo("Information", "No comphep_* folders with files to transfer were found.")

 # === 4. File Mapping and renaming Logic ===
    def toggle_tab(self, folder):
        for tab_id in self.notebook.tabs():
            tab_text = self.notebook.tab(tab_id, option="text")
            if tab_text == folder:
                state = "normal" if self.folder_target_vars[folder]["selected"].get() else "disabled"
                self.notebook.tab(tab_id, state=state)
                break

    def get_default_options(self):
        mode = self.choice_var.get()
        template = self.default_suffixes.get(mode, [])
        options = []
        for idx, parts in enumerate(template, start=1):
            renamed = [self.rename_map.get(p, p) for p in parts]
            options.append(f"{idx}. {'_'.join(renamed)}")
        return options

    def copy_from_first_tab(self):
        tabs = self.notebook.tabs()
        if not tabs:
            return
        first_tab = tabs[0]
        first_folder = self.notebook.tab(first_tab, option="text")
        first_entries = self.file_entries.get(first_folder, [])
        for tab in tabs[1:]:
            folder = self.notebook.tab(tab, option="text")
            entries = self.file_entries.get(folder, [])
            for src, dst in zip(first_entries, entries):
                dst.set(src.get())
# === 5. File transfer and cleanup ===
    def move_files(self):
        m_r = self.m_r_var.get().strip()
        sin_theta = self.sin_theta_var.get().strip()
        lambd = self.lambda_var.get().strip()
        mode = self.choice_var.get()

        if not all([m_r, sin_theta, lambd]):
            messagebox.showerror("Error", "All fields (M_r, sin θ, Lambda) must be filled!")
            return

        new_folder = f"{m_r}_{sin_theta}_{lambd}"
        base_target = os.path.join(os.getcwd(), "organized_output")

        for folder_name, files in self.files_to_rename.items():
            vars = self.folder_target_vars.get(folder_name)
            if not vars or not vars["selected"].get():
                continue

            process = vars["process"].get()
            energy = vars["energy"].get()
            if not process or not energy:
                continue

            entries = self.file_entries.get(folder_name, [])
            target_path = os.path.join(base_target, process, energy, mode, new_folder)
            os.makedirs(target_path, exist_ok=True)

            copied_files = []
            name_set = set()
            for combo in entries:
                name = combo.get().strip()
                if not name:
                    continue
                name_clean = name.split(". ", 1)[1] if ". " in name else name
                if name_clean in name_set:
                    messagebox.showerror("Error", f"Duplicate names in folder {folder_name}: {name_clean}")
                    return
                name_set.add(name_clean)

            for src_file, combo in zip(files, entries):
                name = combo.get().strip()
                if not name:
                    continue
                name = name.split(". ", 1)[1] if ". " in name else name
                safe_name = "".join(c for c in name if c not in '<>:"/\\|?*')
                dst_file = os.path.join(target_path, f"{safe_name}.txt")

                try:
                    shutil.copy2(src_file, dst_file)
                    copied_files.append(src_file)
                    self.append_log(f"{folder_name}: {os.path.basename(src_file)} → {dst_file}")
                except Exception as e:
                    self.append_log(f"Error copying {src_file}: {e}")

            if copied_files:
                answer = messagebox.askyesno("Delete Files?", f"Files from {folder_name} successfully transferred.\nDelete original files?")
                if answer:
                    for f in copied_files:
                        try:
                            os.remove(f)
                            self.append_log(f"Deleted file {os.path.basename(f)} from {folder_name}")
                        except Exception as e:
                            self.append_log(f"Failed to delete {os.path.basename(f)}: {e}")
        messagebox.showinfo("Completed", "File transfer completed.")

# === 6. Launch application ===   
if __name__ == "__main__":
    root = tk.Tk()
    app = FileMoverApp(root)
    root.mainloop()

