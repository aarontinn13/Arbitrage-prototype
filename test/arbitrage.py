import ccxt
from operator import itemgetter

accounts = {'bitstamp': {'uid': 'kwsm6715',
                         'api_key': 'eFrPYCe3KJ2w6aKb6eUYwvBqjdVnkmoU',
                         'secret': '6xc0U55xj4pHJtQDRntzIobGfcoLDlfJ',
                        },

            'binance': {'uid': 'noah13nelson@gmail.com',
                        'api_key': 'oox7xCH0BivEah7LOmfOiHylDEj6tueEArxf3rfj4tgDWFdKNNP9CCNuvKIXxrvR',
                        'secret': 'ouo5WhOL4ISrmbYJcwANcE9piDHG2KvRmQT0i6AJbqabAGSDsxBeHjKpv7RI1VIa',
                       },

            'poloniex': {'uid': 'noah13nelson@gmail.com',
                         'api_key': 'JHGCEVR5-VOLY72AW-ZTDH2DXP-S14TO6KY',
                         'secret': '93475ba24b1a371bbbc07937cfdb5da3f284f389039afba9f90fe208634ff5a6faaedd79e9b2ff14cb937c0c7f9984ee1ce038827038c7dc6447359bead24b8b',
                        },

            'yobit': {'uid': 'noah13nelson@gmail.com',
                      'api_key': '8FA4E982CAB11663C11936006F05097B',
                      'secret': '7ddf527b43a6e876e8dc0a35714bfe2d',
                     },

            'livecoin': {'uid': 'noah13nelson@gmail.com',
                         'api_key': 'YgpVDcsqSdar2YnNyzWhAzxraT2gcHFN',
                         'secret': 't9xm2v8yrhYbfwxMBbQ49huTSDFPBxP3',
                        },

            }



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
    :param accounts: dictionary of exchanges that we own with the account information as their values
    :param ask_market: exchange where we will buy currency
    :param bid_market: exchange where we will sell currency
    :param symbol: (ex. BTC/USD)
    :return: Profit value after the exchange
    '''

    buy_exchange = getattr(ccxt, ask_market)
    sell_exchange = getattr(ccxt, bid_market)

    buy_account = accounts[ask_market]
    sell_account = accounts[bid_market]

    buy = buy_exchange(buy_account)
    sell = sell_exchange(sell_account)

    buy.load_markets()
    sell.load_markets()

    if buy.has['createMarketOrder'] and sell.has['createMarketOrder']:

        buy.createbuymarketorder(symbol, amount) #purchase the currency

        if transfer(buy_account, sell_account, symbol.split('/')[0], amount): #initiate the transfer and check if it returns true.

            sell.create_limit_sell_order(symbol, amount)
            buy_cost = buy.fetch_my_trades(symbol)[-1]['cost']
            print('buy_cost = ' + str(buy_cost))
            sell_cost = sell.fetch_my_trades(symbol)[-1]['cost']
            print('sell_cost = ' + str(sell_cost))
            transfer(sell_account, buy_account, symbol.split('/')[1], (sell_cost-buy_cost))
            return sell_cost - buy_cost

        else:
            return 'transfer unsuccessful'



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
        print('cannot transfer from binance')
        return False

    from_account = getattr(ccxt, from_account)
    from_account = from_account(accounts[from_account])
    to_account = getattr(ccxt, to_account)
    to_account = to_account(accounts[to_account])

    from_account.load_markets()
    to_account.load_markets()

    to = to_account.fetch_deposit_address(curr)
    add = to['address']
    from_account.withdraw(curr, amt, add)

    return 'transfer successful \n {} balance: {} \n {} balance: {}'.format(from_account, from_account.fetch_balance()['info'],
                                                                            to_account, to_account.fetch_balance()['info'])
def main():

    ask_market, bid_market = identify_arbitrage('LTC/USD', exchanges)
    profit = buy_sell(accounts, ask_market, bid_market, 'LTC/USD', 0.1)
    print('Profit earned by the arbitrage trade : ' + str(profit))


if __name__ == '__main__':
    main()