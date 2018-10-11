#!/usr/bin/env python
# coding: utf-8

# In[2]:

import ccxt

from operator import itemgetter

def arbitrage(self, account, symbol):
    print('Arbitrage function started!')

    ask_data = dict()
    bid_data = dict()

    # List of the exchange markets that we want to check the prices in.

    exchanges = ['bitfinex', 'gdax', 'kraken', 'bitlish', 'bitstamp', 'gemini', 'livecoin', 'poloniex', 'exmo',
                 'quoinex', 'itbit', 'lakebtc']

    # Finding the ask and bid prices for every exchange in the exchanges list.

    try:
        for e in exchanges:
            exc = getattr(ccxt, e)()
            exc.load_markets()

            '''
            Create a list of symbols supported by the exchange to make sure that the symbol for which we are doing arbitrage 
            is supported by the exchnage.
            '''

            symbols_allowed = exc.symbols

            if symbol in symbols_allowed:

                # Find the ask and bid price for a given pair of symbols.
                ask_bid_prices = exc.fetch_order_book(symbol)

                # Get just the most recent one value ask and bid prices.
                ask_data[e] = ask_bid_prices['asks'][0][0]
                bid_data[e] = ask_bid_prices['bids'][0][0]

            else:
                pass

        # Sort the ask prices in the ascending order to find the market with the least exchange rate.
        # This market is the place where we want to buy the bitcoin.

        ask_data_sorted = sorted(ask_data.items(), key=itemgetter(1))

        # Sort the bid prices in the descending order to find the market with the least exchange rate.
        # This market is the place where we want to sell the bitcoin.

        bid_data_sorted = sorted(bid_data.items(), key=itemgetter(1), reverse=True)

        # Print the sorted list

        print(ask_data_sorted)
        print(bid_data_sorted)

        # Store the names of the exchange markets.

        ask_market = ask_data_sorted[0][0]
        bid_market = bid_data_sorted[0][0]

        # Print the market names for varification.

        print(ask_market)
        print(bid_market)

        # Create object for market in which we want to buy.

        buy_class = getattr(ccxt, ask_market)()
        buy = buy_class(account)

        # Create object for market in which we want to sell.

        sell_class = getattr(ccxt, bid_market)()
        sell = sell_class(account)

        # Create market buy order.

        if buy.has['createMarketOrder']:
            buy.create_market_buy_order(symbol, 0.01)

            # Retrieve the order data for buy.

            buy_cost = buy.fetch_my_trades(symbol)[-1]['cost']

        # Create market sell order.

        if sell.has['createMarketOrder']:

            sell_data = sell.create_market_sell_order(symbol, 0.01)

            # Retrieve the order data for sell.

            sell_cost = sell.fetch_my_trades(symbol)[-1]['cost']

        # Calculate the arbitrage profit and print it.

        arbitrage_profit = sell_cost - buy_cost

        print('Arbitrage profit =' + str(arbitrage_profit))

    except Exception as e:

        # To print any error encountered during the loop.
        print(e)


# Trial function call to test for a pair of symbols
arbitrage(account, symbol)

# In[28]:

