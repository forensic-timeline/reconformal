Architectural Components
========================

The overall engine is modularized by specific responsibilities mapping forensic records strictly step-by-step:

- **PlasoToFootprint**: Translates generated PLASO timelines to footprint schemas.
- **DataProcessor**: Loads, aggregates, and filters logs recursively across valid CSV directories.
- **EntityExtractor**: Parses normalized footprints to effectively map entries into object/subject records dynamically based on "Event Type" (Web visits, Process Creation, File Access over the file system...).
- **RelationshipManager**: Safely deduplicates identities while sustaining relationships to raw data references. Output relationships are generally split up between 'participation' and 'usage'.
- **KnowledgeRepresentation**: Master orchestrator controlling semantic relationships to unify disparate records.
- **TimelineReconstruction**: Connects chronological timeline sequences linking temporal and structural bounds. Employs the `Correlation_Calculator` executing Allen's interval algebra checks.
- **RelationshipAnalysis**: Aggregates the mathematical coefficients, removes noisy paths (by employing threshold cutoffs filtering irrelevant signals), and initiates summary reports or visual plot outputs.