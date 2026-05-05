.. reconsadfc documentation master file

Welcome to reconsadfc's documentation!
======================================

.. image:: https://img.shields.io/pypi/v/reconsadfc.svg
   :target: https://pypi.org/project/reconsadfc/
.. image:: https://img.shields.io/pypi/pyversions/reconsadfc.svg
   :target: https://pypi.org/project/reconsadfc/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

**Forensic event reconstruction and timeline correlation for SADFC-style data.**

`reconsadfc` is a robust Python library and CLI tool designed for digital forensic investigators and researchers. It provides a DataFrame-first pipeline to process forensic footprint data, extract meaningful relationships (subjects, objects, events), and compute event correlations over time. By inferring and analyzing semantic timelines, it helps uncover complex incident patterns from WEBHIST and other common forensic data sources.

Features
--------

- **Footprint Data Processing**: Seamlessly ingest and filter forensic logs and footprint data.
- **Semantic Entity Extraction**: Automatically isolate subjects, objects, and events from diverse activities.
- **Knowledge Representation Graph**: Support, Participation, and Usage mapping.
- **Temporal & Contextual Correlation Algorithm**: Score and correlate chronological events to filter the timeline, silencing non-essential noise.
- **Built-in Visualization**: Readily generate timeline plots with integrated `matplotlib` support.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   components
   api

