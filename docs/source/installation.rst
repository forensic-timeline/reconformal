Installation
============

You can easily install `reconformal` via PyPI or directly from the source code for development.

From PyPI (Recommended)
-----------------------

Once published, simply run:

.. code-block:: bash

   pip install reconformal

From Source (For Development)
-----------------------------

Clone the repository and install it in editable mode:

.. code-block:: bash

   git clone https://github.com/forensic-timeline/reconformal.git
   cd reconformal
   pip install -e .[test]

Via Docker (No Python Required)
--------------------------------

Build the image locally from the repository root:

.. code-block:: bash

   git clone https://github.com/forensic-timeline/reconformal.git
   cd reconformal
   docker build -t reconformal .

Run the container by mounting your input and output directories:

.. code-block:: bash

   docker run --rm \
     -v /path/to/your/csv/files:/data/input:ro \
     -v /path/to/your/output:/data/output \
     reconformal \
     --input-dir /data/input --output-dir /data/output --threshold 0.0

Add ``--draw-graph`` to also generate a timeline scatter plot saved inside ``/data/output``.

Alternatively, use Docker Compose. Copy ``docker-compose.yml`` from the repo,
place your CSV files in ``./data/input/``, then run:

.. code-block:: bash

   docker compose up

Results will appear in ``./data/output/``.

System Requirements
-------------------
- Python 3.9+
- pandas >= 1.5
- matplotlib >= 3.6