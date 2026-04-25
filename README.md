# reconsadfc

Forensic event reconstruction and relationship analysis for SADFC-style footprint data.

This project provides a DataFrame-first pipeline to:

- filter and preprocess forensic footprint data,
- extract subjects, objects, and events,
- build support and entity-event relationships,
- compute event correlations over time,
- analyze and visualize inferred timelines.

## Features

- Data ingestion and filtering from CSV files (`source == WEBHIST`)
- Entity extraction for common event types (web visit, process creation, search activity, file activity)
- Relationship modeling:
	- footprint-to-entity/event support
	- participation (subject-event)
	- usage (event-object)
- Temporal and contextual correlation scoring
- Timeline filtering based on type-level correlation statistics
- Built-in timeline plotting with Matplotlib

## Installation

### From PyPI

After publishing, install with:

```bash
pip install reconsadfc
```

### From source (local development)

```bash
git clone <your-repository-url>
cd temp-reconformal
pip install -e .
```

## Requirements

- Python 3.9+
- pandas
- matplotlib

## Quick Start

```python
from reconformal import (
		DataProcessor,
		KnowledgeRepresentation,
		TimelineReconstruction,
		RelationshipAnalysis,
)

# 1) Load and filter footprints
processor = DataProcessor(file_dir="./data", save_json=False)
combined_df = processor.process_files()

# 2) Build knowledge representation
kr = KnowledgeRepresentation(combined_df)
kr.sort_data()
kr.extract_entities()

# 3) Reconstruct timeline and compute correlations
timeline_builder = TimelineReconstruction(kr)
timeline_df = timeline_builder.reconstruct_timeline()
correlation_df = timeline_builder.calculate_correlation(timeline_df)

# 4) Analyze timeline quality
analysis = RelationshipAnalysis(kr)
scored_timeline_df = analysis.filter_events_based_on_avg_correlation(
		correlation_df=correlation_df,
		timeline_df=timeline_df,
		threshold=0.0,
)
updated_timeline_df = analysis.update_timeline_df(scored_timeline_df)

# Optional plot
analysis.draw_timeline_graph(updated_timeline_df)

# Optional metrics
counts = analysis.count_classification_groups(updated_timeline_df)
print(counts)
```

## CLI Usage

After installation, run from PowerShell or any shell:

```powershell
reconformal-cli --input-dir .\data --output-dir .\outputs --threshold 0.0 --draw-graph
```

You can also run as a Python module:

```powershell
python -m reconformal --input-dir .\data --output-dir .\outputs
```

Generated outputs are written as CSV files, including timeline, correlation,
relationship, summary, and metrics artifacts.

## Main Components

- `DataProcessor`
	- Reads CSV files from a directory
	- Filters rows where `source` is `WEBHIST`
- `EntityExtractor`
	- Converts footprint rows into normalized subject/object/event records
- `RelationshipManager`
	- Deduplicates entities and builds relationship tables
- `KnowledgeRepresentation`
	- Orchestrates extraction and stores all derived DataFrames
- `TimelineReconstruction`
	- Builds deduplicated timeline and computes pairwise correlations
- `RelationshipAnalysis`
	- Aggregates correlation scores, filters events, enriches timeline, and plots results

## Data Assumptions

Input footprint data is expected to include fields commonly used by the pipeline, such as:

- `id`
- `type`
- `source`
- `date_time_min`
- optional event metadata (for example `keys`, `plugin`, `files`, `filename`)

## PyPI Publishing Checklist

Before publishing, ensure you have:

1. Package metadata configured (`pyproject.toml` preferred).
2. This README referenced as the long description.
3. Version bumped correctly.
4. License file included.
5. Source distribution and wheel built successfully.

Typical commands:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

## Project Structure

Current minimal structure:

- `reconformal/reconformal.py` - core implementation
- `reconformal/cli.py` - CLI parser and command runner
- `reconformal/__main__.py` - module execution entry point
- `reconformal/__init__.py` - package exports
- `pyproject.toml` - packaging metadata and console scripts
- `README.md` - project documentation
- `LICENSE` - MIT license
- `fer-sadfc.ipynb` - notebook exploration

## License

MIT License. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome. Recommended workflow:

1. Open an issue describing the change.
2. Create a feature branch.
3. Add tests and documentation updates.
4. Submit a pull request.
