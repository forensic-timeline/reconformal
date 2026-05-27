Quick Start
===========

`reconformal` works both as a developer-friendly API and an instant Command-Line Interface (CLI) utility.

Python API Example
------------------

Below is an end-to-end example simulating a typical timeline reconstruction pipeline:

.. code-block:: python

   from reconformal import (
       DataProcessor,
       KnowledgeRepresentation,
       TimelineReconstruction,
       RelationshipAnalysis,
   )

   # 1. Load and Preprocess Footprints
   # Ensure your CSV inputs (e.g. from PLASO or WEBHIST tools) are isolated in a folder
   processor = DataProcessor(file_dir="./data")
   combined_df = processor.process_files()

   # 2. Build the Knowledge Representation
   kr = KnowledgeRepresentation(combined_df)
   kr.sort_data()
   kr.extract_entities()

   # 3. Reconstruct Timeline and Calculate Event Correlations
   timeline_builder = TimelineReconstruction(kr)
   timeline_df = timeline_builder.reconstruct_timeline()
   correlation_df = timeline_builder.calculate_correlation(timeline_df)

   # 4. Analyze and Filter Quality of the Timeline
   analysis = RelationshipAnalysis(kr)
   scored_timeline_df = analysis.filter_events_based_on_avg_correlation(
       correlation_df=correlation_df,
       timeline_df=timeline_df,
       threshold=0.0, # adjust based on your tolerance for noise
   )
   updated_timeline_df = analysis.update_timeline_df(scored_timeline_df)

   # 5. (Optional) Visualize Results
   analysis.draw_timeline_graph(updated_timeline_df, output_path="filtered_timeline.png")

   # Output final metrics
   print("Classification Breakdown:\\n", analysis.count_classification_groups(updated_timeline_df))


Command-Line Interface (CLI)
----------------------------

Prefer running terminal commands? `reconformal` bundles a comprehensive CLI that automates all the aforementioned steps automatically.

.. code-block:: bash

   # Process data inside `./data`, output CSV files in `./outputs`, and plot a graph
   reconformal --input-dir ./data --output-dir ./outputs --threshold 0.0 --draw-graph

Alternatively, you could invoke it directly using python:

.. code-block:: bash

   python -m reconformal --input-dir ./data --output-dir ./outputs --draw-graph

Output artifacts inside the destination directory include:

- Cleaned and related entities (`cleaned_entities.csv`)
- Filtered timelines (`updated_timeline.csv`)
- Statistical metrics (`fitness_generalization.csv`, `classification_counts.csv`)