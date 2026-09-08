(**PLEASE** read limitations. There is only so much you can do on free data 😭)
# Methodology 

## Data
Via the [Historical Betfair Portal](https://historicdata.betfair.com.au) I downloaded Australian thoroughbred racing data, specifically filtering for WIN markets across August 2026 and the 
Basic tier package. Basic tier files only contain last traded price per update and do not include any order book depth such as back and lay prices or volume ladders which reduces the type of signal 
I can possibly use to flag.

## Flagging logic 

Each market is only evaluated in the last 90 seconds before a race begins via controlling **window_seconds** and **seconds_to_start** parameters with in-play updates excluded. 
I chose this specific window since it leaves enough room for multiple data updates (BASIC updates every 60 seconds) and that markets on racing are typically the most liquid, especially at larger racing venues like Randwick and Doomben.


