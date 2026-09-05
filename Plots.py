import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("August_results.csv",parse_dates=["race_time"]) #read csv

data=data.sort_values("race_time").reset_index(drop=True) #sort by date

data["wealth"] = data["result"].cumsum() #sum up the results across all races
plt.figure(figsize=(15,5))
plt.plot(data["race_time"],data["wealth"]) #plot the date against cumulative wealth
plt.xlabel("race time")
plt.ylabel("wealth")
plt.title("Arbitrage across August")
plt.show()


