import gzip
import json
import base64
import ast
from botocore.vendored import requests
import pymysql
import sys
import datetime
 
# aws rds mysql
REGION = 'eu-central-1'
rds_host  = "xxxxxx.rds.amazonaws.com"
name = ""
password = ""
db_name = ""

# telegram
token = "xxxxxx:xxxxxx"
chat_id = "" # groupid, channelid or userchatid


def lambda_handler(event, context):
    
    # decoding base64 cloudwatch logs 
    log_events = unzip_payload(event['awslogs']['data'])
    
    for log_event in log_events:
        if "message" in log_event.keys():
            message_dict = ast.literal_eval(log_event["message"])
            if message_dict["event_type"] == "TasksSubmitted":
                print(log_event["message"])
                conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
                increase_score(message_dict,conn)
                insert_label(message_dict, conn)
    
            else:
                print("It doesn't have submission")
        else:
            print("Doesn't have a message body")

def unzip_payload(log_data):
    
    compressed_payload = base64.b64decode(log_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    payload = json.loads(uncompressed_payload)
    log_events = payload['logEvents']
    return log_events
    
        
def increase_score(message_dict, conn):
    
    reaction_time = calculate_reaction(message_dict)
    worker_id = message_dict["cognito_sub_id"]
    
    # only increase score if the reaction_time higher than 4 seconds
    if reaction_time > 4:
        sql = "update users set score = score + 1 where cognito_sub_id = '{}'".format(worker_id)
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            cur.close()
    else:
        print("Score is not updated due to the short reaction time")
    
    send_telegram(worker_id, reaction_time)


def insert_label(message_dict, conn):
    
    reaction_time = calculate_reaction(message_dict)
    cognito_sub_id = message_dict["cognito_sub_id"]
    workteam_arn= message_dict["workteam_arn"]
    labeling_job_arn = message_dict["labeling_job_arn"]
    job_reference_code = message_dict["job_reference_code"]
    
    sql = "INSERT INTO labels (job_reference_code, reaction_time, workteam_arn, labeling_job_arn, cognito_sub_id, timestamp) VALUES (%s, %s, %s, %s, %s, now())"
    val = (job_reference_code, reaction_time, workteam_arn, labeling_job_arn, cognito_sub_id)
    
    with conn.cursor() as cur:
        cur.execute(sql,val)
        conn.commit()
        cur.close()
    
    
def calculate_reaction(message_dict):
    
    submitted_time = message_dict["task_submitted_time"]
    accepted_time= message_dict["task_accepted_time"]

    accepted = datetime.datetime.strptime(accepted_time, '%Y-%m-%dT%H:%M:%S.%f')
    submitted = datetime.datetime.strptime(submitted_time, '%Y-%m-%dT%H:%M:%S.%f')
    diff = (submitted - accepted).total_seconds()
    return diff

def send_telegram(worker_id, reaction_time):
    telegram_msg = "User: {} has just labeled an image with {} sec reaction time!".format(worker_id,reaction_time)
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(token,chat_id,telegram_msg)
    requests.get(url)