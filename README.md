# About
This project is a proof of concept that uses the Flumine and Betfairlightweight API to identify whale behaviour in lay prices and calculate arbitrage between lay prices and delayed bookmaker odds. Below is one such example. This is a VERY simplified model and as such, isn't efficient irl.

Example for August 29, 2026 where back prices are suddenly filled before jump which leads to a low starting price while bookmakers delay behind:

<p align = "center">
  <img src = "images/image_2026-09-05_162252216.png">
  <img src = "images/image_2026-09-05_162340899.png">
</p>

## How to run backtest:

1. Download historical data from the [Betfair Exchange history portal](https://historicdata.betfair.com.au). This downloads as a tar file which you would have to unpack into multiple folders. You can reduce the size of the download by customising filters such as the market type and the country.

<p align = "center">
  <img src = "images/image_2026-09-06_000140354.png" height = 400>
</p>

2.) Find this section of code and replace the path name with your path to the historical data.
<p align = "center">
  <img src = "images/image_2026-09-05_232600469.png">
</p>

3.) After running the code, it will return metrics such as the amount of bets placed and the cumulative wealth at the end of the backtest. 

<img src = "images/image_2026-09-06_221704780.png">

4.) You can also choose to plot the backtest via [Plots.py](Plots.py) 

<img src = "images/image_2026-09-05_163018863.png">

## Parameters:

|Parameter                  | Description                                                                                  |
|-----------------------------|----------------------------------------------------------------------------------------------|
