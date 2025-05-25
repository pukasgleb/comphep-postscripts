# Direct Detection Analysis (LUX-ZEPLIN)

This folder contains a complete and ready-to-use set of scripts for analyzing dark matter direct detection constraints using output from CompHEP simulations. The scripts process theoretical predictions, compare them to experimental limits from the LUX-ZEPLIN experiment, and visualize the allowed parameter regions.

## Purpose

1. **Filter simulated parameter points** based on the value of the predicted cross-section (accepted if below experimental limits).
2. **Select representative values of sin(θ)** according to a custom rule.
3. **Visualize sin(θ)** across a 2D model space defined by `m_hi` and `λ`.

<pre lang="markdown"> ## Folder Structure ```text DirectDetectionAnalyze/ ├── filter_by_experiment.py # Filtering of CompHEP data using LUX-ZEPLIN upper limits ├── interpolate_and_plot.py # Visualizes max sin(θ) from filtered results ├── lux_zeplin.xlsx # Experimental limits on cross-section: sigma_exp(m_exp) ├── filtered_results.xlsx # Output Excel file (created on run, can be regenerated) ├── example_plot.png # Sample 3D plot (can be regenerated) └── ExampleData/ └── 150/ ├── 100.txt ├── 150.txt └── ... # Raw simulation results from CompHEP ``` </pre>
		
## How to Run

### Step 1: Filter the model data	
```bash	
python filter_by_experiment.py 
```

This script:
- reads `lux_zeplin.xlsx` for the experimental limits,
- parses `.txt` files from `ExampleData/150/`,
- selects allowed sin(θ) values per (m_hi, λ) pair,
- saves them to `filtered_results.xlsx`.

### Step 2: Generate a 3D plot
```bash	
python interpolate_and_plot.py
```

This script:
- reads `filtered_results.xlsx`,
- interpolates sin(θ) values,
- saves a 3D plot to `example_plot.png`.