import os
import logging
import urllib
import json
import base64
import gzip
import re

import pymysql
import sys

SLACK_URL = "https://slack.com/api/chat.postMessage"

rds_host = "xxxxxx.eu-central-1.rds.amazonaws.com"
name = "xxxxx"
password = "xxxxx"
db_name = "xxxxx"


def lambda_handler(data, context):
    """Handle an incoming HTTP request from a Slack chat-bot.
    """
    # Grab the Slack event data.
    # decoding base64
    body = base64.b64decode(data['body']).decode("utf-8")
    print(body)

    # finding text part in the long string response
    text = re.search('&text=(.*)&resp', body).group(1)
    user_id = re.search('&user_id=(.*)&user', body).group(1)
    command = re.search('&command=(.*)&text', body).group(1)

    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    if text == "all":
        return score_all(user_id, conn)
    elif text == "today":
        return score_today(user_id, conn)
    else:
        return "Please choose an attribute! `[all]` or `[today]`"


def score_today(user_id, conn):
    sql = """SELECT COUNT(l.job_reference_code)
                FROM users u INNER JOIN
                    labels l
                    ON (l.cognito_sub_id = u.cognito_sub_id and DATE(`timestamp`) = CURDATE() and slack_id = '{}' and l.reaction_time > 4)
                GROUP BY u.cognito_sub_id""".format(user_id)
    with conn.cursor() as cur:
        rows = cur.execute(sql)
        if rows > 0:
            total_score = cur.fetchone()[0]
        else:
            msg = ">Your haven't started labeling today!\n>You need to label *`250`* images to reach *the daily goal!*"
            return msg
        conn.commit()
        cur.close()
    if total_score >= 250:
        msg = ">Your daily successful label count is *`{}`*.\n>You've already reached *the daily goal!*".format(
            total_score)
    else:
        left = 250 - total_score
        msg = ">Your daily successful label count is *`{}`*.\n>You need to label *`{}`* more images to reach *the daily goal!*".format(
            total_score, left)
    return msg


def score_all(user_id, conn):
    sql = "SELECT score FROM groundtruth.users where slack_id = '{}'".format(user_id)
    with conn.cursor() as cur:
        cur.execute(sql)
        total_score = cur.fetchone()[0]
        conn.commit()
        cur.close()
    msg = ">Your total successful label count is *`{}`*".format(total_score)
    return msg
