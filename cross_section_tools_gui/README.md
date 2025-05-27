# Cross Section Analysis Toolkit

This repository contains four Python GUI applications for analyzing and visualizing simulated cross section data from particle physics models (CompHEP output). The tools are designed to assist with browsing, filtering, summing, interpolating, and interactively editing `.txt` files that store cross section vs. mass data.

All scripts are independent but share the same data structure and style.

---

## Directory Structure

All scripts assume the following folder organization:
```
cross_section_tools_gui/							
├── pair production/		          	# Process type 1
│ ├── 14/			                      # √s = 14 TeV center-of-mass energy
│ │ ├── 2X/		                  	  # Final state: 2 particles 
│ │ │ └── M_r_sin_theta_Lambda/			# Fixed parameter configuration 
│ │ │ ├── phi_phi.txt			          # Grid data file (cross-section vs mass) for a specific final state
│ │ │	├── phia_phia_conj.txt		  	# Another final state channel
│ │	│	└── ...
│ │ ├── 3X/			                    # Final state: 3 particles
│ │ ├── 4X/			                    # Final state: 4 particles
│ │ └── Sum/			                  # Auto-generated smoothed sums (created by sum_and_smooth.py)
│ └── 100/			                    # √s = 100 TeV (same internal structure)
├── associated production/		    	# Process type 2
└── weak t-channel process/			    # Process type 3
```

---

## Script Overview

Note: All GUIs require no arguments — just run the script directly.

**Tips:**
- You can drag points on the plot when editing is enabled.
- Edited data is automatically backed up as .bak on first change.
- Plot title fields support full LaTeX syntax (e.g., $\sqrt{s}=14\,\mathrm{TeV}$).
- Saved images are exported in .png at 300 DPI.

### 1. `cross_section_viewer_gui.py`  
**Purpose:**  
Visualize cross-section datasets for a single parameter set (`M_r`, `sinθ`, `Λ`) across multiple final states (`2X`, `3X`, `4X`).

**Key Features:**
- Supports individual or combined view of 2X / 3X / 4X final states  
- Toggle linear/logarithmic X and Y axes  
- LOWESS smoothing with adjustable `frac`  
- Customizable X-axis range  
- Interactive point editing (drag to change values)  
- Save plot as PNG 

---

### 2. `sum_and_plot_gui.py`  
**Purpose:**  
Compute and display the **summed cross section** over multiple final states (2X, 3X, 4X) for multiple parameter sets.

**Key Features:**
- Automatic summation across final states  
- Per-curve smoothing method: `LOWESS`, `PCHIP`, `Spline`, `PolyFit`, or none  
- Custom X-range and per-curve smoothing choice  
- Editable curves: drag to change values  
- Export final plots and data files  

---

### 3. `multiplotter_gui.py`  
**Purpose:**  
Visualize any datasets from input .txt files on a customizable plot.

**Key Features:**
- Add multiple `.txt` files manually  
- Apply smoothing (`LOWESS`, `Spline`, `PCHIP`, `PolyFit`) per file  
- Custom X-range per file  
- Custom legend labels per file  
- Set plot title using LaTeX  
- Save plot as PNG 

---

### 4. `file_sort_gui.py`  
**Purpose:**  
Organize raw `comphep_*` output folders by renaming and moving histogram files into structured final-state directories.

**Key Features:**
- Automatically detect `comphep_*` folders  
- Assign process type, energy, and final state  
- Auto-rename files according to final state configuration  
- Copy files to `process/energy/final_state/M_r_sinθ_Λ/` structure  
- Optional cleanup: delete original files after transfer  

---


### Requirements
The code is written in Python 3.9+ and uses the following Python libraries:

- `tkinter`
- `matplotlib`
- `pandas`
- `numpy`
- `statsmodels`
- `scipy`
