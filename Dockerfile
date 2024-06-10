# Use the official Miniconda3 image
FROM continuumio/miniconda3

# Set environment variables for Conda
ENV CONDA_ENV=clinical_trial_data_pipeline
ENV PATH /opt/conda/envs/$CONDA_ENV/bin:$PATH

# Copy environment.yml to create the Conda environment
COPY environment.yml /tmp/environment.yml

# Create the Conda environment
RUN conda env create -f /tmp/environment.yml

# Initialize Conda and activate the environment
RUN echo "source activate $CONDA_ENV" >> ~/.bashrc

# Install necessary packages in the Conda environment
RUN /bin/bash -c "source activate $CONDA_ENV && pip install apache-airflow==2.9.1 flask transformers torch duckdb tqdm dlt openai"

# Set the working directory
WORKDIR /app

# Copy the project files
COPY clinical_trial_data_pipeline /app

# Initialize the Airflow database
RUN /bin/bash -c "source activate $CONDA_ENV && airflow db init"

# Create the necessary Airflow directories
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins

RUN mkdir -p /opt/airflow/.dbt

# Copy the Airflow DAGs and other necessary files
COPY clinical_trial_data_pipeline/src/dags /opt/airflow/dags
COPY clinical_trial_data_pipeline/src /opt/airflow/src

# Copy the .env file
COPY .env /opt/.env
COPY clinical_trial_data_pipeline/src/models/profiles.yml /opt/airflow/.dbt/profiles.yml

# Load environment variables from .env file
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# Set environment variables for Flask and Airflow
ENV FLASK_APP=/opt/airflow/src/models/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV AIRFLOW_HOME=/opt/airflow
ENV DUCKDB_PATH=/opt/airflow/src/data/clinical_trial_data.duckdb
ENV DBT_HOME=/opt/airflow/.dbt

# Expose the ports for Airflow web server, scheduler, and Flask
EXPOSE 8080 8793 5002

# Set the entry point for the container
ENTRYPOINT ["/bin/bash", "-c"]

# Command to start both Airflow scheduler, webserver, and Flask app
CMD ["source activate $CONDA_ENV && airflow scheduler & airflow webserver & flask run --host=0.0.0.0 --port=5002"]