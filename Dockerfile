# Use the official Miniconda3 image
FROM continuumio/miniconda3

# Create the Conda environment
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# Make sure the environment is activated
SHELL ["conda", "run", "-n", "clinical_trial_data_pipeline", "/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Copy the project files
COPY clinical_trial_data_pipeline /app

# Initialize the Airflow database
RUN airflow db init

# Create the necessary Airflow directories
RUN mkdir -p /usr/local/airflow/dags

# Copy the Airflow DAGs
COPY clinical_trial_data_pipeline/src/dags /usr/local/airflow/dags

# Expose the ports for Airflow web server and Flask
EXPOSE 8080 8793 5000

# Set environment variables for Flask
ENV FLASK_APP=/app/src/models/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV AIRFLOW_HOME=/usr/local/airflow

# Set the entry point for the container
ENTRYPOINT ["conda", "run", "-n", "clinical_trial_data_pipeline", "sh", "-c"]

# Command to start both Airflow scheduler, webserver, and Flask app
CMD ["airflow scheduler & airflow webserver & flask run --host=0.0.0.0"]
