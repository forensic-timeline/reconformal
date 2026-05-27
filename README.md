# reconformal

[![PyPI version](https://badge.fury.io/py/reconformal.svg)](https://badge.fury.io/py/reconformal)
[![Python Version](https://img.shields.io/pypi/pyversions/reconformal.svg)](https://pypi.org/project/reconformal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Forensic event reconstruction and relationship analysis for SADFC-style footprint data.

This project provides a DataFrame-first pipeline to:

- Filter and preprocess forensic footprint data,
- Extract subjects, objects, and events,
- Build support and entity-event relationships,
- Compute event correlations over time,
- Analyze and visualize inferred timelines.

## Features

- Data ingestion and filtering from Plaso CSV files
- Entity extraction for common event types (web visit, process creation, search activity, file activity)
- Relationship modeling:
  - Footprint-to-entity/event support
  - Participation (subject-event)
  - Usage (event-object)
- Temporal and contextual correlation scoring
- Timeline filtering based on type-level correlation statistics
- Built-in timeline plotting with Matplotlib

## Installation

### From PyPI

Install the package directly from PyPI (once published):

`bash
pip install reconformal
`

### From source (local development)

`bash
git clone https://github.com/forensic-timeline/reconformal
cd reconformal
pip install -e .
`

### Via Docker (No Python Required)

Build the image locally from the repository root:

`bash
git clone https://github.com/forensic-timeline/reconformal
cd reconformal
docker build -t reconformal .
`

Run by mounting your input CSV files and an output directory:

`bash
docker run --rm \
  -v /path/to/your/csv/files:/data/input:ro \
  -v /path/to/your/output:/data/output \
  reconformal \
  --input-dir /data/input --output-dir /data/output --threshold 0.0
`

Or with Docker Compose — place your CSV files in `./data/input/` and run:

`bash
docker compose up
`

Results will appear in `./data/output/`.

## Requirements

- Python 3.9+
- pandas >= 1.5
- matplotlib >= 3.6

## Quick Start

The easiest way to use the library is via the 
un_pipeline function mapping, which automates file reading and DataFrame generation.

`python
from reconformal import run_pipeline

# Run the complete reconstruction pipeline
outputs = run_pipeline(
    input_dir="./data",
    output_dir="./outputs",
    threshold=0.0,
    draw_graph=True,
    graph_filename="filtered_timeline.png"
)

# Access individual generated datasets
timeline_df = outputs['timeline_df']
correlation_df = outputs['correlation_df']
print("Generated Timeline Records:", len(timeline_df))
`

### Advanced Usage (Step-by-step)
If you need finer execution control, you can import individual modules:
`python
from reconformal import DataProcessor, TimelineReconstruction, RelationshipAnalysis
from reconformal.reconformal import KnowledgeRepresentation

# 1) Load and filter footprints
processor = DataProcessor(file_dir="./data")
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
`

## CLI Usage

After installation, run from PowerShell or any shell:

`bash
reconformal --input-dir ./data --output-dir ./outputs --threshold 0.0 --draw-graph
`

You can also run as a Python module:

`bash
python -m reconformal --input-dir ./data --output-dir ./outputs
`

Generated outputs are written as CSV files, including timeline, correlation, relationship, summary, and metrics artifacts.

## Main Components

- DataProcessor: Reads CSV files from a directory and combines valid forensic evidence.
- PlasoToFootprint: Processes and detects appropriate browser/system entities based on Plaso evidence definitions.
- EntityExtractor: Converts footprint rows into normalized subject/object/event records.
- RelationshipManager: Deduplicates entities and builds relationship tables.
- TimelineReconstruction: Builds deduplicated timeline and computes pairwise correlations.
- RelationshipAnalysis: Aggregates correlation scores, filters events, enriches timeline, and plots results.

## Data Assumptions

Input footprint data is expected to include fields commonly used by the pipeline from Plaso CSVs:

- parser
- message
- display_name
- datetime
- filename

## Project Structure

- 
reconformal/reconformal.py - Core implementation and pipeline
- 
reconformal/__main__.py - Module execution entry point
- 
reconformal/__init__.py - Package exports
- pyproject.toml - Packaging metadata and console scripts
- 	ests/ - Unit tests for package modules
- docs/ - Sphinx documentation files
- README.md - Project documentation
- LICENSE - MIT license

## License

MIT License. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome. Recommended workflow:

1. Open an issue describing the change.
2. Create a feature branch.
3. Add tests and documentation updates.
4. Submit a pull request.
