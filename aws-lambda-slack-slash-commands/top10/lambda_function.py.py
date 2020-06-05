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

rds_host = "xxxxx.rds.amazonaws.com"
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
    sql = """SELECT COUNT(l.job_reference_code),
                u.name, u.team
            FROM users u INNER JOIN
                 labels l
                 ON (l.cognito_sub_id = u.cognito_sub_id and DATE(`timestamp`) = CURDATE() and l.reaction_time > 4)
            GROUP BY u.cognito_sub_id
            ORDER BY COUNT(job_reference_code) DESC
            LIMIT 10
                    """
    msg = create_response(conn, sql)

    return msg


def score_all(user_id, conn):
    sql = """SELECT score, name, team from users
             ORDER BY score DESC
             LIMIT 10
                    """
    msg = create_response(conn, sql)

    return msg


def create_response(conn, sql):
    with conn.cursor() as cur:
        rows = cur.execute(sql)
        conn.commit()
        if rows > 0:
            tagger_list = cur.fetchall()
            cur.close()

            msg = '\n```'
            header = "======== =================== =========== =============== \n| Order |       Name         |  Score   |      Team     |\n======== =================== =========== =============== \n"
            msg = msg + header
            total_score = 0
            for i, tag in enumerate(tagger_list):
                score, tagger, team = tag
                tagger = '{:^20}'.format(tagger)
                count = '{:^8}'.format(i + 1)
                total_score = total_score + score
                score = '{:^10}'.format(score)
                team = '{:^15}'.format(team)
                line = "{}|{}|{}|{}|\n".format(count, tagger, score, team)
                msg = msg + line
            msg = msg + "```\n" + ">*Sum of the tags of the top 10:* `{}`".format(total_score)
            return msg
        else:
            msg = ">There is no labelers today! You need to label *`250`* images to reach *the daily goal!*"
            return msg

