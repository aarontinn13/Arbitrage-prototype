import ccxt
from operator import itemgetter

exchanges = ['bitstamp', 'binance', 'livecoin', 'yobit', 'poloniex']

def identify_arbitrage(symbol, exchange_list):

    '''
    Finds lowest ask and highest bid for a currency in given exchanges
    :param symbol: (ex. BTC/USD)
    :param exchanges: pass EXCHANGES above or another list of exchanges
    :return: ((ask,ask_price),(bid, bid_price)
    '''
    
    ask_data = dict()
    bid_data = dict()

    for e in exchange_list:
        exc = getattr(ccxt, e)()
        exc.load_markets()
        symbols_allowed = exc.symbols
        
        if symbol in symbols_allowed:

            ask_bid_prices = exc.fetch_order_book(symbol)
            ask_data[e] = ask_bid_prices['asks'][0][0]
            bid_data[e] = ask_bid_prices['bids'][0][0]
            
        else:
            continue

    ask_data_sorted = sorted(ask_data.items(), key=itemgetter(1))
    bid_data_sorted = sorted(bid_data.items(), key=itemgetter(1), reverse=True)

    print(ask_data_sorted)
    print(bid_data_sorted)

    ask_market = ask_data_sorted[0][0]
    bid_market = bid_data_sorted[0][0]

    print('market to buy from : ' + str(ask_market))
    print('market to sell in : ' + str(bid_market))

    return ask_market, bid_market

def buy_sell(accounts, ask_market, bid_market, symbol, amount):

    '''
    Initiate a transaction between accounts and exchanges
    :param account1: account where we will buy currency
    :param account2: account where we will sell currency
    :param exchange1: exchange where we will buy currency
    :param exchange2: exchange name where we will sell currency
    :param symbol: (ex. BTC/USD)
    :return: Nothing
    '''

    buy_exchange = getattr(ccxt, ask_market)
    sell_exchange = getattr(ccxt, bid_market)

    account1 = accounts[ask_market]
    account2 = accounts[bid_market]

    buy = buy_exchange(account1)
    sell = sell_exchange(account2)

    buy.load_markets()
    sell.load_markets()

    if buy.has['createMarketOrder'] and sell.has['createMarketOrder']:
    
        buy.createbuymarketorder(symbol, amount)
        transfer(account1, account2, symbol.split('/')[0], amount)
        sell.create_limit_sell_order(symbol, amount)

    buy_cost = buy.fetch_my_trades(symbol)[-1]['cost']
    print('buy_cost = ' + str(buy_cost))

    sell_cost = sell.fetch_my_trades(symbol)[-1]['cost']
    print('sell_cost = ' + str(sell_cost))
    
    return (sell_cost - buy_cost)

def check_balance(account, exchange):

    '''
    Check the balance of an account in an exchange
    :param account: account we will check
    :param exchange: exchange with the account
    :return: information and balance in a tuple structure.
    '''
    
    info = getattr(ccxt, exchange)
    info = info(account)
    info.load_markets()
    info = info.fetch_balance()

    return (info['info']['balances'])

def transfer(from_account, to_account, curr, amt):

    '''
    :param from_account: name of exchange we are transferring from
    :param to_account: name of exchange we are transferring to
    :param curr: name of the currency
    :param amt: amount
    :return: return success or error and balance
    '''

    if from_account == 'binance':
        return 'cannot transfer from binance'

    from_account = getattr(ccxt, from_account)
    from_account = from_account(accounts[from_account])
    to_account = getattr(ccxt, to_account)
    to_account = to_account(accounts[to_account])

    from_account.load_markets()
    to_account.load_markets()

    to = to_account.feath_deposit_address(curr)

    add = to['address']

    from_account.withdraw(curr, amt, add)

    return 'transfer successful \n {} balance: {} \n {} balance: {}'.format(from_account, from_account.fetch_balance()['info'] ,

                                                                            to_account.fetch_balance()['info'], to_account)


ask_market, bid_market = identify_arbitrage('LTC/USD', exchanges)
profit = buy_sell(accounts, ask_market, bid_market, 'LTC/USD', 0.1)
print('Profit earned by the arbitrage trade : ' + str(profit))
