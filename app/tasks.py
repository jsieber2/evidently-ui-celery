from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from datetime import datetime
import pandas as pd
from sklearn import datasets
from evidently.ui.workspace import Workspace
import os

import create_functions

MESSAGE_QUEUE_URL = os.getenv('MESSAGE_QUEUE_URL', 'redis://localhost:6379')

# Define app with a local redis broker
# Docker-compose fills in the relevant network details
app = Celery('tasks', broker=MESSAGE_QUEUE_URL)



# Define project specifications here
WORKSPACE = "workspace"
PROJECT_NAME = "My First MLOps Project"
PROJECT_DESCRIPTION = "Evidently AI + Celery"


# This "create" function actually performs a get_or_create function 
# within the evidently package
workspace = Workspace.create(WORKSPACE)
project = create_functions.get_or_create_project(workspace,PROJECT_NAME,PROJECT_DESCRIPTION)

@app.task
def daily_task():
    print("Running daily task...")
    print('A celery task! This runs every two minutes.')
    with open('/app/output.txt', 'a') as f:
        f.write('Task executed at {}\n'.format(datetime.now()))


@app.task 
def monitor_task_1():
    # we will run this every minute, so it loops from 0 to 4 repeatedly
    # This is where you would add your own evidently monitoring report creation
    i = datetime.now().minute % 5

    #initiate datasets from the evidently tutorial
    adult_data = datasets.fetch_openml(name="adult", version=2, as_frame="auto")
    adult = adult_data.frame
    adult_ref = adult[~adult.education.isin(["Some-college", "HS-grad", "Bachelors"])]
    adult_cur = adult[adult.education.isin(["Some-college", "HS-grad", "Bachelors"])]


    project = create_functions.get_or_create_project(workspace,PROJECT_NAME,PROJECT_DESCRIPTION)

    report = create_functions.create_report(i=i,reference_df=adult_ref,current_df=adult_cur)
    workspace.add_report(project.id, report)

    test_suite = create_functions.create_test_suite(i=i,reference_df=adult_ref,current_df=adult_cur)
    workspace.add_test_suite(project.id, test_suite)
    return 'Monitoring Ran Successfully'





app.conf.beat_schedule = {
    'daily_task': {
        'task': 'tasks.daily_task',
        #'schedule': crontab(minute=0, hour=0), # Run every day at midnight
        'schedule': timedelta(minutes=2), # Run every two minutes

    },
    'monitor_task_1':{
       
        'task': 'tasks.monitor_task_1',
        'schedule': timedelta(minutes=1), # Run every minute

    
    }
}