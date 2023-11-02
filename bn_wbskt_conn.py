# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import pandas as pd
import json

import time
import logging
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

from google.cloud import bigquery
from google.oauth2 import service_account
# -

config_logging(logging, logging.DEBUG)


def message_handler(_, message):
    
    # Collect msg converting to DataFrame
    lst = []
    
    msg = json.loads(message)
    
    msg['event_time'] = msg.pop('E')
    msg['t_time'] = msg.pop('T')
    msg['m_i'] = msg.pop('M')
    
    lst.append(msg)
    credentials = service_account.Credentials.from_service_account_file(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],filename="C:/Users/Ponlawat Hongkoed/Downloads/regal-mediator-403517-b50f4905a3e4.json"
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id,)
    
    rows_to_insert = lst
    
    # regal-mediator-403517.bn_tesing.bn_trade_stream1
    
    errors = client.insert_rows_json("regal-mediator-403517.bn_tesing.bn_trade_stream1", rows_to_insert)  # Make an API request.
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
    
    logging.info(message)


def stream_to_bq():

    my_client = SpotWebsocketStreamClient(on_message=message_handler)
    my_client.trade(symbol="btcusdt")
    time.sleep(5)
    logging.debug("closing ws connection")
    my_client.stop()


if __name__ == "__main__":
    stream_to_bq()
    
