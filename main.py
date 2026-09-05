
from flumine import FlumineSimulation, BaseStrategy, clients
from flumine.markets.market import Market
from betfairlightweight.resources import MarketBook
import glob
import os
from concurrent import futures
import math
import csv
import pandas as pd

#---------------------------------------------
def chunks(lst, n): #function for splitting files to processes
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def seconds_to_jump(market_book: MarketBook): #Function defines how much time before race starts
    market_def = market_book.market_definition
    if not market_def or not market_def.market_time or not market_book.publish_time: #If there isn't anything in the market def or anything related to time, we return none
        return None
    return (market_def.market_time - market_book.publish_time).total_seconds() #We return the difference in race time and Betfair data update (only interested in seconds)

def detection_window(market_book: MarketBook, window_seconds = 90) -> bool: #Call seconds to jump to see if the time till race starts is between variable "window_seconds"
    seconds = seconds_to_jump(market_book)
    if seconds is None:
        return False
    return 0 <= seconds <= window_seconds #returns True if this inequality

#------------------------------------------------
class WhaleArb(BaseStrategy):

    def __init__(self, stake = 50,commission = 0.08,*args,**kwargs):
        super().__init__(*args,**kwargs) #using base strategy parent class arguments cause time involved
        self.stake = stake #parameter for staking
        self.commission = commission #parameter for betfair commission
        self.window_entry_price = {} #record the entry price
        self.window_entry_time = {} #record times when price is recorded
        self.already_flagged = {} #Only used for recording if a certain runner has been flagged
        self.pending_results = {} #Used to store key info about runners, runner results, price etc...
        self.total_flags = 0 #Used to flag any bets we take if price drop is above certain threshold
        self.total_wealth = 0 #Used to track the total wealth across the month

    def check_market_book(self, market: Market, market_book: MarketBook): #Note that other functions from BaseStrategy will not run if you don't include this
        if market_book.status != "CLOSED":
            return True #Market is running if not closed

    def process_market_book(self, market: Market, market_book: MarketBook): #This is used for processing data inside the individual market
        if not detection_window(market_book):
            return

        market_id = market_book.market_id
        entry_prices = self.window_entry_price.setdefault(market_id, {}) #populate the entry_price dictionary with the market id and a place to store entry prices
        entry_time = self.window_entry_time.setdefault(market_id, {}) #populate the entry_time dictionary with the market id and a place to store times
        flagged = self.already_flagged.setdefault(market_id, set()) #populate the dictionary with market id and a set for whether or not runner ids are stored

        for runner in market_book.runners:
            current_price = runner.last_price_traded # we store the current price of the runner as the last price traded
            current_time = seconds_to_jump(market_book) # stores the current time

            if current_price is None or current_price == 0: #don't have any previous price to compare to so we ignore
                continue

            if runner.selection_id not in entry_prices:
                entry_prices[runner.selection_id] = current_price #store the current price related to selection id
                entry_time[runner.selection_id] = current_time #store the current time related to selection id
                continue

            if runner.selection_id in flagged: #if its flagged, we don't want to keep flagging
                continue

            reference_price = entry_prices[runner.selection_id] #we get a delayed price from the entry price dictionary
            reference_time = entry_time[runner.selection_id] # we get the time related to that reference price

            percentage_drop = ((reference_price - current_price) / reference_price )* 100 #calculate the percentage drop in price between the old and current price

            entry_prices[runner.selection_id] = current_price #store the new current price to be used for later reference price
            entry_time[runner.selection_id] = current_time #store the time with that too

            if percentage_drop >= 10 and current_price <= 10: #can change these parameters but if the percentage drop > smth and if the current price < smth (to reduce betfair liability)
                race_time = market_book.market_definition.market_time #store the actual date
                flagged.add(runner.selection_id) #flag the runner, make sure it doesn't appear again (cause set)
                self.total_flags += 1 # increase bet
                self.pending_results.setdefault(market_id,[]).append({ # append to the list bunch of metrics, metrics are self-explanatory
                    "selection_id": runner.selection_id,
                    "race_time": race_time,
                    "time_till_jump": seconds_to_jump(market_book),
                    "reference_price": reference_price,
                    "reference_time": reference_time,
                    "price_at_flag": current_price,
                    "time_at_flag": current_time,
                    "percentage_drop": percentage_drop
                })

    def process_closed_market(self, market: Market, market_book: MarketBook) -> None: # Part of Base Strategy which processes market closure
        sp_by_selection = {r.selection_id: r.sp.actual_sp for r in market_book.runners} #dictionary that pairs selection id with the bsp before jump
        status_by_selection = {r.selection_id: r.status for r in market_book.runners} #dictionary that pairs selection id with the result (Win or Loss)

        for flag in self.pending_results.get(market_book.market_id, []): # iterates over list corresponding to market_id
            racer_id = flag["selection_id"]

            actual_sp = sp_by_selection.get(racer_id)
            flag["bsp"] = actual_sp #add element for the bsp before race

            flag["outcome"] = status_by_selection.get(racer_id)  #add element for win/loss

            lay_stake = (self.stake * flag["reference_price"])/(flag["price_at_flag"]) #This is arb stake on betfair (MENTION LIMITATIONS tho)
            profit = lay_stake*(1-self.commission) - self.stake #how much we expect to make from both sides (bookie/betfair)

            flag["result"] = profit #add element for the outcome
            flag["market_id"] = market_book.market_id #add the market id
            self.total_wealth += profit #update the total wealth

#-------------------------------

def run_process(markets): #we wrap it in a function for later
    client = clients.SimulatedClient() #Call on the simulated client
    framework = FlumineSimulation(client=client) # again, specifically simulation command for flumine

    strategy = WhaleArb(
        market_filter = {
        "markets":markets,
        'market_types': ['WIN'], #Bit redundant since I specifically ordered the August package and filtered for win markets previously
        'country_codes': ['AU'], #Same thing as above but useful ig if you want to change countries or markets
        "listener_kwargs": {"inplay": False, "seconds_to_start":90} # we limit the time to 90 seconds before jump and we don't want to do anything after race starts
    },
    )
    framework.add_strategy(strategy)
    framework.run()

    out_path = f"whale_results_{os.getpid()}.csv" # we save the result (of each process) to a unique csv file
    file_exists = os.path.exists(out_path)
    with open(out_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "market_id", "selection_id","race_time", "reference_price","reference_time", "price_at_flag", "time_at_flag", #These are our columns
                "percentage_drop", "actual_sp", "outcome", "result",
            ])
        for flags in strategy.pending_results.values():
            for flag in flags:
                writer.writerow([
                    flag["market_id"], flag["selection_id"],flag["race_time"], flag["reference_price"], flag["reference_time"], #populate with the corresponding values
                    flag["price_at_flag"],flag["time_at_flag"] ,flag["percentage_drop"], flag["bsp"],
                    flag["outcome"], flag["result"],
                ])

    return strategy.total_flags, strategy.total_wealth

if __name__ == "__main__":
    data_files = glob.glob(
        "D:/backtest_data/BASIC/2026/Aug/***/**/*.bz2", recursive=True  #go through every single file in the dir where I saved the data
    )
    print(f"Found {len(data_files)} files")

    if not data_files:
        raise SystemExit("No data")

    #I took most of this code from the Betfair Automation hub part 5, specifically about optimising cpu usage for multiprocessing
    all_markets = data_files
    processes = os.cpu_count()
    markets_per_process = 8
    chunk_size = min(markets_per_process, math.ceil(len(all_markets)/processes))

    print(f"Running {processes} processes with {chunk_size} files per batch")

    _process_jobs = []
    with futures.ProcessPoolExecutor(max_workers=processes) as p:
        for m in chunks(all_markets, chunk_size):
            _process_jobs.append(p.submit(run_process, m))

        total_flags = 0
        total_wealth = 0.0
        for job in futures.as_completed(_process_jobs):
            flags, profit = job.result()
            total_flags += flags
            total_wealth += profit

    print(f"Total bets: {total_flags}")
    print(f"Cumulative wealth: {total_wealth:.2f}")

    individual_files = glob.glob("whale_results_*.csv")

    #combine the individual files
    if individual_files:
        combined = pd.concat(
            (pd.read_csv(f) for f in individual_files), ignore_index=True
        )
        combined.to_csv("August_results.csv", index=False)
        print(f"Combined {len(individual_files)} files with {len(combined)} rows")

        for f in individual_files: #Remove the junk files
            os.remove(f)
    else:
        print(f"No files were found")
