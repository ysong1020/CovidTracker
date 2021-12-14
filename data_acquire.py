"""
covid-19 data, US, New York Times
"""
import time
import sched
import pandas as pd
import numpy as np
import logging
import requests
import pymongo
from io import StringIO
import utils


MAX_DOWNLOAD_ATTEMPT = 10

urls = {'us': 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv', 
        'states': 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'}

filters = {'us': ['date'],
           'states': ['date', 'state']}

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

def upsert_data(df, geo='us'):
    db = client.get_database(geo)   
    collection = db.get_collection(geo) 
    update_count = 0
    for record in df.to_dict('records'):
        #print(record)
        result = collection.replace_one(
            filter={_:record[_] for _ in filters[geo]},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count += 1
    print(f'{geo}:', 
          f'rows={df.shape[0]}, update={update_count}, '
          f'insert={df.shape[0]-update_count}')

def update_once():
    for geo, url in urls.items():
        t = download_data(url)
        df = filter_data(t)
        upsert_data(df, geo)


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