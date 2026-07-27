# Imaging Data Organization Workflow
This workflow reformats outputs from the imaging processing pipelines into standardized analysis-ready tables. It combines participant and session information with imaging quality-control measures and regional FreeSurfer outputs, resolving differences in file structure, naming conventions, laterality, metrics, and atlas organization across processing streams.

## [`01_organize.py`](01_organize.py)
Builds a subject-session reference table and converts configured FreeSurfer summary files into a common long-format dataset. The script links imaging outputs to participant and scan identifiers, calculates age at acquisition, includes Euler number quality-control measures, standardizes regional and laterality labels, and assigns cortical regions to lobes where applicable.

The workflow is configured using a JSON file specifying the reference datasets, FreeSurfer input tables, atlas labels, and output directory.
```python organize.py ../config/organize.json```

**Output:**
- Subject-session reference table: `derivatives/dataset/subjects_sessions.csv`
- Standardized regional imaging table: `derivatives/dataset/imaging_data.csv`