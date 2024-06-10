# Clinical Trial Data Pipeline

This project provides a comprehensive data pipeline for clinical trial data, leveraging tools like Apache Airflow, DBT, DuckDB, and Flask. The pipeline processes clinical trial data, generates embeddings, and serves a web application for patient-to-trial matching.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker
- Docker Compose
- Git

## Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/grp-dalida-data/clinical_trial_data_pipeline.git
   cd clinical_trial_data_pipeline
   ```

2. **Set up environment variables:**:

```sh
DUCKDB_PATH=/app/src/data/clinical_trial_data.duckdb
OPENAI_API_KEY=<api_key>
```

3. **Build and start the Docker containers**:

```sh
docker-compose build
docker-compose up

docker-compose run airflow-webserver airflow db init
```

4. **Initialize the Airflow database**:
```sh
docker-compose run airflow-webserver airflow db init
```

Usage

Access the Airflow UI:

Open your browser and navigate to http://localhost:8081 to access the Airflow webserver.

Trigger the DAG:

The DAG is scheduled to run monthly. You can manually trigger it via the Airflow UI.
The DAG executes the following steps:
Run main.py to process the data.
Run DBT models to transform the data.
Run generate_embeddings_and_load.py to generate and load embeddings.
Access the Flask web application:

Open your browser and navigate to http://localhost:5001 to access the Flask web application for patient-to-trial matching.