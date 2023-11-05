# binance_streaming

# Binance Websocket Stream
Hi! this is the easy way to start exploring about Binance Websocket Connector and build streaming dashboard
by using public python library [binance-conector](https://github.com/binance/binance-connector-python/blob/master/README.md).

First of all, this is the overview architecture.
![binance_stream (2)](https://github.com/PonlawatRocket/binance_streaming/assets/149598125/b1033e42-f91a-46d0-b602-3a365de347b2)

To start running pipeline, you can do step-by-step following.
## Create Service Account
1. Go to Google Cloud Console. Search "Service Account" in search bar.
2. Create Service Account by assigning "BigQuery Admin" role.
3. Done
## Create Compute Engine (GCE)
1. Go to Google Cloud Console. Search "Compute Engine"
2. Click "Create Instance" to create virtual machine
3. Done
## Create BigQuery Table 
1. Go to Google Cloud Console. Search "BigQuery"
2. Choose your default project. Create dataset `testing`.
3. Create landing layer `landing_bn_stream`. Indicate data type all as needed.
## Run pipeline via GCE
1. Start virtual machine via "SSH".
2. Clone this repository by command `git clone <repository>`
3. Any updated version, using `<your project path>\ git pull`
4. Run python file `python3 bnn_wbskt_conn.py`
5. Application will ask running time to stream websocket data until stopping. Input running time in minute or 0 for running forever.
![image](https://github.com/PonlawatRocket/binance_streaming/assets/149598125/8f2031ab-4b09-4e88-8d39-b7fd48dba80a)
![image](https://github.com/PonlawatRocket/binance_streaming/assets/149598125/aaec2578-62cc-4b6c-95cd-6796ab18d6d6)

Data will stream in to BigQuery first layer (landing table). As of now, start creating next layer (view) to prepare data in proper format. 
```SQL
### Intermediate Layer

SELECT
event_type
, TIMESTAMP_MILLIS(event_time)  as  event_time
, symbol
, TIMESTAMP_MILLIS(CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.t')  AS  INT64))  AS  kline_start_time
, TIMESTAMP_MILLIS(CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.T')  AS  INT64))  AS  kline_close_time
, JSON_EXTRACT_SCALAR(kline_desc, '$.i')  AS  time_interval
, JSON_EXTRACT_SCALAR(kline_desc, '$.f')  AS  first_trade_id
, JSON_EXTRACT_SCALAR(kline_desc, '$.L')  AS  last_trade_id
, JSON_EXTRACT_SCALAR(kline_desc, '$.o')  AS  open_price
, JSON_EXTRACT_SCALAR(kline_desc, '$.c')  AS  close_price
, JSON_EXTRACT_SCALAR(kline_desc, '$.h')  AS  high_price
, JSON_EXTRACT_SCALAR(kline_desc, '$.l')  AS  low_price
, CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.v')  AS  FLOAT64)  AS  base_asset_volume
, CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.n')  AS  INT64)  AS  number_of_trades
, JSON_EXTRACT_SCALAR(kline_desc, '$.x')  AS  is_this_kline_closed
, CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.q')  AS  FLOAT64)  AS  quote_asset_volume
, CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.V')  AS  FLOAT64)  AS  taker_buy_base_asset_volume
, CAST(JSON_EXTRACT_SCALAR(kline_desc, '$.Q')  AS  FLOAT64)  AS  taker_buy_quote_asset_volume
FROM  `regal-mediator-403517.bn_tesing.landing_bn_stream`
WHERE  JSON_EXTRACT_SCALAR(kline_desc, '$.x')  LIKE  'true'
```
```SQL
### Final Layer

WITH  qr_trades  AS  (
SELECT
"01 Number of Trades"  AS  dims
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  5  MINUTE)  THEN  number_of_trades  END)  AS  last_5_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  10  MINUTE)  THEN  number_of_trades  END)  AS  last_10_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  15  MINUTE)  THEN  number_of_trades  END)  AS  last_15_minutes
FROM  `regal-mediator-403517.bn_tesing.int_bn_stream`
), qr_bought  AS  (
SELECT
"02 Number of Bought Quantity (BTC)"  AS  dims
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  5  MINUTE)  THEN  base_asset_volume  -  taker_buy_base_asset_volume  END)  AS  last_5_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  10  MINUTE)  THEN  base_asset_volume  -  taker_buy_base_asset_volume  END)  AS  last_10_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  15  MINUTE)  THEN  base_asset_volume  -  taker_buy_base_asset_volume  END)  AS  last_15_minutes
FROM  `regal-mediator-403517.bn_tesing.int_bn_stream`
), qr_sold  AS  (
SELECT
"03 Number of Sold Quantity (BTC)"  AS  dims
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  5  MINUTE)  THEN  taker_buy_base_asset_volume  END)  AS  last_5_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  10  MINUTE)  THEN  taker_buy_base_asset_volume  END)  AS  last_10_minutes
, SUM(CASE  WHEN  kline_close_time  >=  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL  15  MINUTE)  THEN  taker_buy_base_asset_volume  END)  AS  last_15_minutes
FROM  `regal-mediator-403517.bn_tesing.int_bn_stream`
), qr_ratio  AS  (
SELECT
"04 Ratio between Quantity Bought and Sold (BTC)"  AS  dims
, qb.last_5_minutes/qs.last_5_minutes  AS  last_5_minutes
, qb.last_10_minutes/qs.last_10_minutes  AS  last_10_minutes
, qb.last_15_minutes/qs.last_15_minutes  AS  last_15_minutes
FROM  qr_bought  qb  CROSS  JOIN  qr_sold  qs
)
SELECT  *  FROM  qr_trades  UNION  ALL
SELECT  *  FROM  qr_bought  UNION  ALL
SELECT  *  FROM  qr_sold  UNION  ALL
SELECT  *  FROM  qr_ratio
ORDER  BY  dims
;
```
## Connect to Looker Studio and Build Dashboard
1. Go to Looker Studio
2. Add data source and set data freshness to "1 minute".
3. Build Dashboard >> [Binance BTC Streaming Report](https://lookerstudio.google.com/reporting/be27f7b1-b62f-4f75-8682-4e4c91c7f528)

![image](https://github.com/PonlawatRocket/binance_streaming/assets/149598125/bb3a95d8-d654-4155-89d9-0298b671ad8e)

