(**PLEASE** read limitations. There is only so much you can do on free data 😭)
# Methodology 

## Data
Via the [Historical Betfair Portal](https://historicdata.betfair.com.au) I downloaded Australian thoroughbred racing data, specifically filtering for WIN markets across August 2026 and the 
Basic tier package. Basic tier files only contain last traded price per update and do not include any order book depth such as back and lay prices or volume ladders which reduces the type of signal 
I can possibly use to flag.

## Flagging logic 

Each market is only evaluated in the last 90 seconds before a race begins via controlling **window_seconds** and **seconds_to_start** parameters with in-play updates excluded. 
I chose this specific window since it leaves enough room for multiple data updates (BASIC updates every 60 seconds) and that markets on racing are typically the most liquid, especially at larger racing venues like Randwick and Doomben. This also means that there is enough liquidity for whales to get filled on back contracts which would provide an arbitrage opportunity if such an event happened. 

<p align = "center">
  (Insert link to betfair market context) 
</p>
<p align = "center">
  <img src = "images/image_2026-09-07_233144022.png" height = 400>
</p>

For a market that does have a jump time within the 90 seconds, during each market update, we loop through each runner and track their selection id, last price traded and the time remaining till jump. Because we only have last price traded to rely upon, we track a "percentage" drop.

$$ P_{drop} = \frac{P_{n} - P_{n-1}}{\Delta*t} *100$$

Additionally, we track a maximum on the lay prices for mainly two reasons. That being there isn't much liquidity on longshots which would impact how much of an order you would get filled at. Moreover, lay bets operate on a liability 
