"""
covid-19 data, US, New York Times
"""
import time
import sched
import pandas as pd
import numpy as np
import logging
import requests
import pymango
from io import StringIO
import utils

from database import upsert_data

MAX_DOWNLOAD_ATTEMPT = 10

urls = {'counties': 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv',
        'states': 'https://github.com/nytimes/covid-19-data/blob/master/us-states.csv',
        'us': 'https://github.com/nytimes/covid-19-data/blob/master/us.csv'}



DOWNLOAD_PERIOD = 24*3600         # second --> every 24 hrs

logger = logging.Logger(__name__)

utils.setup_logger(logger, 'data.log')

client = pymongo.MongoClient()

def download_data(url=urls['us'], retries=MAX_DOWNLOAD_ATTEMPT):
    """Returns covid cases and deaths data in the US from `urls` that includes multiple links
    Returns None if network failed
    """
    text = None
    for i in range(retries):
        try:
            req = requests.get(url, timeout=0.5)
            req.raise_for_status()
            text = req.text
        except requests.exceptions.HTTPError as e:
            logger.warning("Retry on HTTP Error: {}".format(e))
    if text is None:
        logger.error('download_data too many FAILED attempts')
    return text


def filter_data(text):
    """Converts `text` to `DataFrame`, removes empty lines and descriptions
    """
    # use StringIO to convert string to a readable buffer
    df = pd.read_csv(StringIO(text), delimiter=',') 
    df.columns = df.columns.str.strip()             # remove space in columns name  
    df['date'] = pd.to_datetime(df['date']) 
    df.dropna(inplace=True)             # drop rows with empty cells
    return df


def update_once():
    t = download_data()
    df = filter_data(t)
    upsert_bpa(df)


def main_loop(timeout=DOWNLOAD_PERIOD):
    scheduler = sched.scheduler(time.time, time.sleep)

    def _worker():
        try:
            update_once()
        except Exception as e:
            logger.warning("main loop worker ignores exception and continues: {}".format(e))
        scheduler.enter(timeout, 1, _worker)    # schedule the next event

    scheduler.enter(0, 1, _worker)              # start the first event
    scheduler.run(blocking=True)


if __name__ == '__main__':
    main_loop()


