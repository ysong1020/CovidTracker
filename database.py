import logging
import pymongo
import pandas as pds
import expiringdict
import time
import utils

client = pymongo.MongoClient()
logger = logging.Logger(__name__)
utils.setup_logger(logger, 'db.log')
RESULT_CACHE_EXPIRATION = 3600 * 24            # seconds

geo = ['us','states','counties']

def fetch_all_data():
    db = client.get_database("us")
    ret_dict = {}
    for i in geo:
        length = 0
        while length == 0:
            collection = db.get_collection(i)
            ret = list(collection.find())
            ret_dict[i] = ret
            length = len(ret)
            if length == 0:
                time.sleep(30)
            logger.info(str(length) + ' documents read from the db')
        time.sleep(1)
    return ret_dict


_fetch_all_data_as_df_cache = expiringdict.ExpiringDict(max_len=10,
                                                       max_age_seconds=RESULT_CACHE_EXPIRATION)


def fetch_all_data_as_df(allow_cached=False):
    """Converts list of dicts returned by `fetch_all_data` to DataFrame with ID removed
    Actual job is done in `_worker`. When `allow_cached`, attempt to retrieve timed cached from
    `_fetch_all_data_as_df_cache`; ignore cache and call `_work` if cache expires or `allow_cached`
    is False.
    """
    def _work():
        ret_dict = fetch_all_data()
        if len(ret_dict) == 0:
            return None
        df_dict = {}
        for geo, data in ret_dict.items():
            df = pd.DataFrame.from_records(data)
            df.drop('_id', axis=1, inplace=True)
            df.columns = map(str.lower, df.columns)
            df_dict[geo] = df
        return df_dict

    if allow_cached:
        try:
            return _fetch_all_data_as_df_cache['cache']
        except KeyError:
            pass
    ret = _work()
    _fetch_all_data_as_df_cache['cache'] = ret
    return ret


if __name__ == '__main__':
    print(fetch_all_data_as_df())

