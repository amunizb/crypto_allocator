#Crypto allocation
#This is a variation that (tries to) makes sure the current top 10 cyptos have correct weighting (ignoring the money allocated to other cyptos)
#This might make sense because top 10 is not stable so we don't want to get rid of cryptos 11, 12 etc??
#Instead of recalculating weights after a coin's investevement doesn't reach cutoff, we keep original weights and redeistribute proportionally (see ignore function)
from requests import Request, Session
import json
import pprint #pretty print

class coin:
    def __init__(self, name, marketcap, price):
        self.name = name
        self.marketcap = marketcap
        self.price = price

def call_api():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest' #where to fetch the data (change sandbox by pro for non-test)

    parameters = {
        'start':'1',  #start with crypto 1
        'limit':'200',   #end with crypto 200
        'convert' : 'USD'
    }
    headers = {
        'Accepts' : 'application/json', #end format (xlm also supported)
        'X-CMC_PRO_API_KEY' : 'ad5a51de-29eb-4ead-8e66-13f37a5ca152' #unique KEY to get data
    }

    session = Session()
    session.headers.update(headers)  #update default headers to the ones specified above

    response = session.get(url,params=parameters) #call the data
    return json.loads(response.text) #format it nicely: json.loads makes sure it comes out in a json file (as opposed to a string or so) - essentially it will add spaces and some formatting toresponse.text
    #pprint.pprint(data) #pretty print; use to visualize where the info we want is

def get_top_10(data):
    i = 0  # Coin index
    top_coins = []
    while len(top_coins) < 10:
        price = data['data'][i]['quote']['USD']['price']
        # Exclude stable coins
        if 0.99 < price and price < 1.01:  
            i = i + 1  # move to next coin
            continue
        else:
            name, marketcap, price = data['data'][i]['name'], data['data'][i]['quote']['USD']['market_cap'], data['data'][i]['quote']['USD']['price']
            top_coins.append(coin(name,marketcap,price))
            i = i + 1  # move to next coin
    # Now we have top 10 cyptos by market cap
    return top_coins

def read_current_holdings():
    import os
    import pandas as pd
    from datetime import date

    # Get the current date
    filename = "data/my_holdings.csv"
    
    if os.path.exists(filename):
        # Open and read the file
        with open(filename, mode='r') as file:
            df = pd.read_csv(file, index_col='Name')
    else:
        # Prompt the user for input to create a new file
        print("Let's create a CSV file with your holdings.")
        current_date = date.today()
        data = {'Name':[],current_date:[]}
        rows = []
        while True:
            name = input("Enter crypto name (or 'q' to quit): ")
            if name == 'q':
                break
            holding = input("Enter your current holding (in cryptos): ")
            data['Name'].append(name)
            data[current_date].append(holding)  # Collect rows as lists
            
        # Write the new file
        df = pd.DataFrame(data)
        df.set_index('Name', inplace=True)

        df.to_csv(filename)
    current_holdings = pd.DataFrame(df[df.columns[-1]])
    current_holdings.index = df.index
    return current_holdings

def get_conversion_rate(from_currency, to_currency):
    import requests

    api_key = "3666edbc7d884b0883793973eb0cba04"
    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"

    response = requests.get(url)
    data = response.json()
    gbp_to_usd = data['rates']['USD'] / data['rates']['GBP']  # Conversion rate GBP to USD
    return gbp_to_usd
def actualize_coins(top_coins,data):
    x = ""
    print("Input the symbol (eg BTC) of any other crypto you hold:")
    while x != "0":
        x = input()
        if x == "":
            break
        i = 0
        while data["data"][i]["symbol"] != x:
            i = i + 1
        top_coins["name"].append(data['data'][i]['name'])
        top_coins["marketcap"].append(data['data'][i]['quote']['USD']['market_cap'])
    return top_coins

def total(top_coins, attribute):
    total = 0
    for c in top_coins:
        total += getattr(c, attribute)
    return total 

def ignore(top_coins, sequential='no'):

    amounts_to_add = [c.amount_to_add for c in top_coins]

    #Check if elimination is necessary at all
    if min(amounts_to_add) >= 10:
        return top_coins

    n = len(top_coins)

    #Global quantities
    total_marketcap = total(top_coins, 'marketcap')
    total_holding = total(top_coins, 'current_holding')

    

    for c in top_coins:
        c.weight = c.marketcap/total_marketcap
        

    #Start elimination
    while len(top_coins) > 0 and min(amounts_to_add) < 10:
        # Calculate the required investments to reach the minimum threshold for each coin
        investments_needed = [(c.current_holding + cut_off) / c.weight - total_holding for c in top_coins] 
        minimun_investment_needed = max(investments_needed) # The most problematic coin
        k = investments_needed.index(minimun_investment_needed)  # Locate problematic coin
        

        if sequential == "yes":
            # THIS PART OF THE CODE WON'T WORK

            print("Your current investments would be: ")
            for i in range(n):
                print(f"{names[i]}: £{round(amounts_to_add[i],2)}")

            decision = input(f"Some of your investments are not enough for Binance's minimum. You should be investing £{round(minimun_investment_needed,2)} if you want to invest in these {n} cryptos. Do you want to do this? (yes/no) ")
            if decision == "yes":
                for i in range(len(names)):
                    amounts_to_add[i] = weights[i] * (total_holding + minimun_investment_needed) - holdings[i]
                break
            elif decision == "no":
                pool = amounts_to_add[k]
                del names[k]
                del marketcaps[k]
                del holdings[k]
                del amounts_to_add[k]
                del weights[k]
                total_holding = sum(holdings)
                weights = [weights[i] / sum(weights) for i in range(len(weights))]#Normalise weights after eliminating one of them
                #would it be better to compute the weights again?
                for i in range(n-1):
                    amounts_to_add[i] += pool*weights[i]
            else:
                print("Sorry I did not understand you.")
            absolutes = [abs(ele) for ele in amounts_to_add]
        elif sequential == "no":
            pool = top_coins[k].amount_to_add
            del top_coins[k]
            total_marketcap = total(top_coins, 'marketcap')
            total_holding = total(top_coins, 'current_holding')
            
            for c in top_coins:
                c.weight = c.marketcap/total_marketcap

            total_weight = total(top_coins, 'weight')
            for c in top_coins:
                c.amount_to_add += pool * c.weight / total_weight
        else:
            print("Sorry I did not understand you.")
        
        amounts_to_add = [c.amount_to_add for c in top_coins]
    return top_coins

def print_amounts_to_buy():
    print("You should buy:")
    for c in top_coins:
        print(c.name+": $"+str(round(c.amount_to_add, 2)))
def update_current_holdings(top_coins):
    import pandas as pd
    from datetime import date
    # Load the existing CSV file into a DataFrame
    file_path = 'data/my_holdings.csv'  # Replace with your CSV file path
    df = pd.read_csv(file_path, index_col='Name')
    col_number = len(df.columns)

    current_date = date.today()

    # List of coin names and corresponding values
    coins = [c.name for c in top_coins]
    coin_values = [(c.amount_to_add + c.current_holding)/c.price for c in top_coins] #(recall c.current_holding is in USD)

    # Create a dictionary from the list of coins and their values
    coin_dict = dict(zip(coins, coin_values))

    # Iterate through the coin names and check if they are in the DataFrame
    for coin in coin_dict.keys():
        if coin in df.index:  # Check if the coin already exists
            # Add a new column with the value from the list
            df.loc[coin, current_date] = coin_dict[coin] 
        else:
            # If the coin does not exist, create a new row
            new_row = [0] * col_number + [coin_dict[coin]]  # First column is coin name, rest are 0s
            df.loc[coin] = new_row  # Append the new row to the DataFrame

    # Copy the last column's values to the next column for rows that haven't been modified
    df[df.columns[-1]] = df[df.columns[-1]].fillna(df[df.columns[-2]])

    # Save the modified DataFrame back to the CSV file
    df.to_csv(file_path)

cut_off = 10  # Minimum investment allowed by Binance

#Get data from Coinmarketcap API (top 200 coins)
data = call_api() 

#Get top 10 cryptos (names and marketcap)
top_coins = get_top_10(data) 
print("Here is a list of the top 10 coins by marketcap this month: ")
for i, coin in enumerate(top_coins):
    print(f"{i+1}. {coin.name}")

#Todo: Think about consdiring other coins that I also hold
#top_coins = actualize_coins(top_coins,data) #Include other coins that I currently hold

current_holdings = read_current_holdings()

for c in top_coins:
    if c.name in current_holdings.index:
        current_holding_c = current_holdings.loc[c.name, current_holdings.columns[-1]]
        # Current holding in USD (current_holdings stores number of coins)
        c.current_holding = current_holding_c * c.price
    else:
        c.current_holding = 0
print("Your current holdings are: ")
for c in top_coins:
    print(f"{c.name}: ${round(c.current_holding, 2)}")
investment  = input("How much money are you adding this month (in GBP)? ")
# Compute investment in USD
investment = float(investment) * get_conversion_rate('GBP','USD')


total_holding = total(top_coins, "current_holding")
total_marketcap = total(top_coins, "marketcap")

for c in top_coins:
    quantity = (c.marketcap/total_marketcap) * (total_holding+investment) - c.current_holding #Amount to add/sell according to current holding and marketcap weight
    c.amount_to_add = quantity

print(f'Original amount to buy = {sum(c.amount_to_add for c in top_coins)}\n')
#  #Decide between sequential or full (all at once) elimination
# sequential = input("Would you like to see a sequential elimination? (yes/no)")
top_coins = ignore(top_coins) #Eliminate iteratively all coins with abs(amount_to_add) less than 10, asking first whether we want to increase investment
print_amounts_to_buy()


update_current_holdings(top_coins)
