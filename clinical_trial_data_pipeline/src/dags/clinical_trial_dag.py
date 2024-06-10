from __future__ import annotations

import logging
import sys
import time
from pprint import pprint
from datetime import timedelta

import pendulum

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash_operator import BashOperator


log = logging.getLogger(__name__)

PATH_TO_PYTHON_BINARY = sys.executable

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2024, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

parent_dag = DAG(
    dag_id = "clinical_trial_dag",
    default_args=default_args,
    description='Clinical Trial Data Pipeline',
    schedule_interval='@monthly',
    catchup=False,
)

run_main_script = BashOperator(
    task_id='run_main_py',
    bash_command='pip install tqdm && \
        pip install dlt && \
        pip install dlt[duckdb] && \
        pip install transformers && \
        pip install openai && \
        pip install torch && \
        ls /opt/airflow/src/data/ && \
        python /opt/airflow/src/main.py',
    dag=parent_dag,
)

run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='pip install dbt-core && \
    pip install dbt-duckdb &&\
    cd /opt/airflow/src/models/dbt_models && \
    dbt run --models custom_eligibility_criteria.sql --profiles-dir /opt/airflow/src/models',
    dag=parent_dag
)

run_generate_embeddings = BashOperator(
    task_id='run_generate_embeddings',
    bash_command='pip install sentence-transformers &&\
        pip install dlt &&\
        python /opt/airflow/src/models/generate_embeddings_and_load.py',
    dag=parent_dag,
)

    # Set task dependencies
run_main_script >> run_dbt >> run_generate_embeddings