#! /usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
import docker
import sched
import time

from main import instagram_robot

s = sched.scheduler(time.time, time.sleep)


def send_email(email, password, message):

    smtp_ssl_host = "smtp.gmail.com"  # smtp.mail.yahoo.com
    smtp_ssl_port = 465
    targets = ["ss.elmachehour@gmail.com"]

    msg = MIMEText(message)
    msg["Subject"] = "Container is down"
    msg["From"] = email
    msg["To"] = ", ".join(targets)

    server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
    server.login(email, password)
    server.sendmail(email, targets, msg.as_string())
    server.quit()


def get_all_running_containers():
    client = docker.from_env()  # DockerClient(base_url='tcp://127.0.0.1:2375')
    return client.containers.list()


def get_coontainer_status(name: str):
    client = docker.from_env()
    for e in client.containers.list():
        if e.name == name:
            return e.status
    raise Exception("Container not found")


def checker(container_name: str):
    status = get_coontainer_status(container_name)
    if status != "running":
        send_email(
            "issam.elmachehour@evead.com",
            "37004FB915",
            f"<h1>{instagram_robot} is down</h1>",
        )
    s.enter(60, 1, checker, argument=(container_name,))


if __name__ == "__main__":
    s.enter(10, 1, checker, argument=("instagram_robot",))
    s.run()
