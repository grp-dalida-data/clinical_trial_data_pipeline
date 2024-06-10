from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os
import subprocess


def run_main_script():
    subprocess.run(["python", "/usr/local/airflow/src/main.py"], check=True)

def run_dbt():
    subprocess.run(["dbt", "run", "--models", "custom_eligibility_criteria.sql"], cwd="/usr/local/airflow/src/models/dbt_models", check=True)

def run_generate_embeddings():
    subprocess.run(["python", "/usr/local/airflow/src/models/generate_embeddings_and_load.py"], check=True)

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'clinical_trial_data_pipeline',
    default_args=default_args,
    description='A clinical trial data pipeline',
    schedule_interval='@monthly',
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task 1: Run main.py
    run_main_py = PythonOperator(
        task_id='run_main_script',
        python_callable=run_main_script,
    )

    # Task 2: Run dbt
    run_dbt = PythonOperator(
        task_id='run_dbt',
        python_callable=run_dbt,
    )
    # Task 3: Run generate_embeddings_and_load.py
    run_generate_embeddings_and_load_py = PythonOperator(
        task_id='run_generate_embeddings',
        python_callable=run_generate_embeddings,
    )
    # Define task dependencies
    run_main_py >> run_dbt >> run_generate_embeddings_and_load_py