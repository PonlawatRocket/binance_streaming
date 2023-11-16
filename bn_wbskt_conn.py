
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

print("Enter your run time (minute) (0 for run forever):")
run_time = int(input())
run_time = run_time*60

# +
#print(run_time)

# +
# k_line_stream
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
    
    # Manipulate message to JSON (payload)
    lst = []
    msg = json.loads(message)
    
    if msg['k']['x']: 
        
        msg['event_type'] = msg.pop('e')
        msg['event_time'] = msg.pop('E')
        msg['symbol'] = msg.pop('s')
        msg['kline_desc'] = msg.pop('k')

        msg['kline_desc'] = json.dumps(msg['kline_desc'])

        lst.append(msg)
        rows_to_insert = lst
        
        # Connect to BiqQuery 
        client = bigquery.Client()
        
        # Insert JSON 
        errors = client.insert_rows_json("regal-mediator-403517.bn_tesing.landing_bn_stream", rows_to_insert)  # Make an API request.
        if errors == []:
            print("New rows have been added.")
        else:
            print("Encountered errors while inserting rows: {}".format(errors))
    
        logging.info(message)


def insert_to_bq(run_time=run_time, symbol="btcusdt", interval="1m"):

    my_client = SpotWebsocketStreamClient(on_message=message_handler)

    if run_time > 0:
        # subscribe btcusdt 1m kline
        my_client.kline(symbol=symbol, interval=interval)
        
        time.sleep(run_time)

        # unsubscribe btcusdt 1m kline
        my_client.kline(
            symbol=symbol, interval=interval, action=SpotWebsocketStreamClient.ACTION_UNSUBSCRIBE
        )

        time.sleep(5)

        logging.debug("closing ws connection")
        my_client.stop()
    
    elif run_time == 0:
        
        # subscribe btcusdt 1m kline
        my_client.kline(symbol=symbol, interval=interval)
    
    else:
        print("error for connecting")
        my_client.stop()


if __name__ == "__main__":
    insert_to_bq()

#Hello

