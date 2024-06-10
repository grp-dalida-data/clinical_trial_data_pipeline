# Use the official Miniconda3 image
FROM continuumio/miniconda3

# Add conda to the path so we can execute it by name
ENV PATH=/opt/conda/clinical_trial_data_pipeline/bin:$PATH

# Copy environment.yml to the Docker container
COPY environment.yml /tmp/environment.yml

# Update conda and create the environment
RUN conda update -n base conda -y && conda install -n base pip -y
RUN conda env create -f /tmp/environment.yml

# Activate the environment
RUN echo "conda activate clinical_trial_data_pipeline" >> ~/.bashrc

# Set the working directory
WORKDIR /app

# Copy the project files
COPY clinical_trial_data_pipeline /app

# Activate the conda environment and initialize the Airflow database
RUN /bin/bash -c "source ~/.bashrc && conda activate clinical_trial_data_pipeline && airflow db init"

# Create the necessary Airflow directories
RUN mkdir -p /usr/local/airflow/dags

# Copy the Airflow DAGs and src files
COPY clinical_trial_data_pipeline/src/dags /usr/local/airflow/dags
COPY clinical_trial_data_pipeline/src /usr/local/airflow/src

# Expose the ports for Airflow web server and Flask
EXPOSE 8080 8793 5001

# Set environment variables for Flask and Airflow
ENV FLASK_APP=/app/src/models/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV AIRFLOW_HOME=/usr/local/airflow
ENV DUCKDB_PATH=/app/src/data/clinical_trial_data.duckdb

# Set the entry point for the container
ENTRYPOINT ["/bin/bash", "-c"]

# Command to start both Airflow scheduler, webserver, and Flask app
CMD ["source ~/.bashrc && conda activate clinical_trial_data_pipeline && airflow scheduler & airflow webserver & flask run --host=0.0.0.0"]
