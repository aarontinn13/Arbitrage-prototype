import ccxt
from operator import itemgetter
import time

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
                         'api_key': 'fVKyf8EyTMD4gsvZ3KneYB8WEBpeKqhH',
                         'secret': '5h4XPCRnt9AraXePPEfJQfP6mjs9YspN',
                         },

            }

exchanges = ['bitstamp', 'binance', 'livecoin', 'yobit', 'poloniex']
alternate_coins = ['BTC', 'LTC', 'ETH', 'ZEC', 'DASH', 'XRP', 'XMR', 'BCH', 'NEO', 'ADA', 'EOS']
stable_coins = ['USDT', 'TUSD', 'DAI']

global buy_id, sell_id, cancel_id, b_exc, s_exc, buy_stable_id, sell_stable_id

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

    if (len(ask_data_sorted) == 0 and len(bid_data_sorted) == 0):
        print('No exchanges found that support the currencies!')
    elif (len(ask_data_sorted) == 1 and len(bid_data_sorted) == 1):
        if ask_data_sorted[1][0] == bid_data_sorted[1][0]:
            print('currencies not supported by enough exchanges to find arbitrage opportunities!')
    else:
        a = [len(ask_data_sorted), len(bid_data_sorted)]
        refund_symbol = False
        for i in range(min(a)):
            ask_market = ask_data_sorted[i][0]
            ask_price = ask_data_sorted[i][1]
            for j in range(min(a)):
                bid_market = bid_data_sorted[j][0]
                bid_price = bid_data_sorted[j][1]
                if (ask_market != bid_market):
                    refund_symbol = check_refund_possibility(stable_coins, symbol, ask_market, bid_market)
                    print('symbol = ' + str(refund_symbol))
                    if refund_symbol:
                        break
            if refund_symbol:
                break

    if (refund_symbol == False) and (i == min(a) - 1):
        flag_2 = True
    else:
        flag_2 = False

    print('market to buy from : ' + str(ask_market))
    print('market to sell in : ' + str(bid_market))

    return ask_market, bid_market, ask_price, bid_price, flag_2, refund_symbol


def buy_sell(accounts, ask_market, bid_market, ask_price, bid_price, symbol, amount, flag, refund_symbol):
    '''
    Initiate a transaction between accounts and exchanges
    :param accounts: dictionary of exchanges that we own with the account information as their values
    :param ask_market: exchange where we will buy currency
    :param bid_market: exchange where we will sell currency
    :param symbol: (ex. BTC/USD)
    :return: Profit value after the exchange
    '''

    if flag:
        return 'Could not find a pair of exchanges that support stable coins! \nThus cannot do Arbitrage!'

    if ask_market == bid_market:
        return 'No arbitrage possibilies were found!'

    buy_exchange = getattr(ccxt, ask_market)
    sell_exchange = getattr(ccxt, bid_market)

    buy_account = accounts[ask_market]
    sell_account = accounts[bid_market]

    buy = buy_exchange(buy_account)
    sell = sell_exchange(sell_account)

    buy.load_markets()
    sell.load_markets()
    '''Refund symbol is the symbol that has stable coin as the base currency.
    This symbol will be used to buy stable coin in sell market, send it to the buy market,
    and sell in the buy market to get back the quote currency. This will complete the arbitrage.'''

    # refund_symbol = check_refund_possibility(stable_coins,symbol,ask_market,bid_market)

    '''Refund symbol = False if both the exchanges do not have the same stable coin!
    Else it will contain the pair of currency symbol, i.e., Satble_coin_symbol/original_quote_symbol.'''

    if refund_symbol == 'False':

        return 'Arbitrage is not possible because the exchanges do not support the stable coins!'

    else:

        '''To store the price of the stable coin that will be used to create limit order for buying and selling the coins!'''

        refund_cur_price = sell.fetch_order_book(refund_symbol)['asks'][0][0]

        # if check_status(b_exc,s_exc,buy_id,sell_id,cancel_id,buy_stable_id,sell_stable_id):

        '''Check if the previous arbitrage has been completed!'''
        b_exc = ask_market
        s_exc = bid_market

        if buy.has['createMarketOrder'] and sell.has['createMarketOrder'] and refund_symbol != False:

            buy_id = buy.create_limit_buy_order(symbol, amount, ask_price)['id']  # purchase the currency

            '''Create a buy order for the main arbitrage base currency.'''

            if transfer(ask_market, bid_market, symbol.split('/')[0],
                        amount):  # initiate the transfer and check if it returns true.

                '''Create a sell order for the main arbitrage base currency.'''

                sell_id = sell.create_limit_sell_order(symbol, amount, bid_price)['id']
                profit = calculate_profit(b_exc, s_exc, buy_id, sell_id, amount) - (
                        refund_cur_price * amount_refund * 0.002)
                '''Create a buy order for the stable coin.'''
                amount_refund = profit / refund_cur_price
                buy_stable_id = sell.create_limit_buy_order(refund_symbol, amount_refund, refund_cur_price)['id']

                if transfer(ask_market, bid_market, symbol.split('/')[0], amount):
                    sell_stable_id = buy.create_limit_sell_order(refund_symbol, amount_refund, refund_cur_price)['id']

                    # buy_cost = buy.fetch_my_trades(symbol)[-1]['cost']
                # sell_cost = sell.fetch_my_trades(symbol)[-1]['cost']
                # print('sell_cost = ' + str(sell_cost))
                # print('buy_cost = ' + str(buy_cost))
                profit = (bid_price * amount * 0.998) - (ask_price * amount * 1.002)
                print('Buy_id = ' + str(buy_id))
                print('Sell_id = ' + str(sell_id))
                print('Buy_stable_id = ' + str(buy_stable_id))
                print('Sell_stable_id = ' + str(sell_stable_id))
                return 'Arbitrage successful! \nProbable profit earned: ' + str(profit)
            else:

                '''Resell the bought coins in case the transfer does not occur!
                Also use the cancel_id to make sure that the reselling of the coins is complete before
                starting a new arbitrage.'''

                cancel_id = buy.create_limit_sell_order(symbol, amount, bid_price)['id']

            return 'Transfer unsuccessful! The bought currency is sold back!'

        return 'Arbitrage could not be done as some exchange does not support stable coins!'

    # return 'Previous arbitrage left to be completed!'


def transfer(from_market, to_market, curr, amt):
    '''
    :param from_account: name of exchange we are transferring from
    :param to_account: name of exchange we are transferring to
    :param curr: name of the currency
    :param amt: amount
    :return: return success or error and balance
    '''

    def timing():

        '''re run this function until the transfer is complete'''
        if check_balance(accounts, to_market, curr)[1] != to_balance_prior_transfer:
            return True
        return False

    if from_market == 'binance':
        print('cannot transfer from binance')
        return False

    from_exchange = getattr(ccxt, from_market)
    from_account = from_exchange(accounts[from_market])
    to_exchange = getattr(ccxt, to_market)
    to_account = to_exchange(accounts[to_market])

    from_account.load_markets()
    to_account.load_markets()

    to_balance_prior_transfer = check_balance(accounts, to_market, curr)

    to = to_account.fetch_deposit_address(curr)
    add = to['address']
    from_account.withdraw(curr, amt, add)

    start = time.time()
    while True:
        end = time.time()
        if timing():
            return True
        elif end - start > 3600:  # 1 hour
            return False


def check_balance(accounts, exchange, curr):
    '''
    Check the balance of an account in an exchange
    :param account: list of accounts above
    :param exchange: exchange with the account we are checking
    :return: information and balance in a tuple structure.
    '''

    info = getattr(ccxt, exchange)
    info = info(accounts[exchange])
    info.load_markets()
    info = info.fetch_balance()

    return (curr, info['total']['{}'.format(curr)])


def check_status(b_ex, s_ex, b_id, s_id, c_id, b_stable_id, s_stable_id):
    if b_ex and s_ex:
        b = getattr(ccxt, b_ex)(accounts[b_ex])
        s = getattr(ccxt, s_ex)(accounts[s_ex])
        b.load_markets()
        s.load_markets()
    else:
        return True

    if b_id:

        b_status = b.fetchOrder(b_id)['status']

    else:

        b_status = False

    if s_id:

        s_status = s.fetchOrder(s_id)['status']

    else:

        s_status = False

    if b_stable_id:

        b_stable_status = s.fetchOrder(b_stable_id)['status']

    else:

        b_stable_status = False

    if s_stable_id:

        s_stable_status = b.fetchOrder(s_stable_id)['status']

    else:

        s_stable_status = False

    '''If buy and sell orders for the normal coin and the stable coin are filled return True to indicate end of arbitrage.'''

    if b_status == 'closed' and s_status == 'closed' and b_stable_status == 'closed' and s_stable_status == 'closed':

        '''After all the orders are filled(i.e., the arbitrage is complete) we set the order ids and the order status 
        to false! It is to show that we have completed the arbitrage and are ready for the next arbitrage!'''

        buy_id = False
        sell_id = False
        buy_stable_id = False
        sell_stable_id = False
        b_status = False
        s_status = False
        b_stable_status = False
        s_stable_status = False

        return True

    else:

        return False

    if c_id:

        c = getattr(ccxt, b_ex)(accounts[b_ex])
        c.load_markets()
        c_status = c.fetchOrder(c_id)['status']

        if c_status == 'closed':
            cancel_id = False

            return True

    return False


def check_refund_possibility(stable_coins, symbol, b_ex, s_ex):
    base_curr = symbol.split('/')[0]
    quote_curr = symbol.split('/')[1]
    b = getattr(ccxt, b_ex)(accounts[b_ex])
    s = getattr(ccxt, s_ex)(accounts[s_ex])
    b.load_markets()
    s.load_markets()
    b_sym = b.symbols
    s_sym = s.symbols
    if len(b_sym) < len(s_sym):
        test = b_sym
    else:
        test = s_sym
    for a in stable_coins:

        '''Create a symbol where the base is stable coin and the quote is the original quote.'''

        temp = a + '/' + quote_curr

        '''Check if the symbol is supported by both the exchanges.'''
        if ((temp in b_sym) and (temp in s_sym)):
            refund_symbol = temp
            break
        else:
            refund_symbol = False
    if not refund_symbol:
        print('\nThis is the information while searching for the alternate coins! Just to visualise what the function is doing!')
        print('Displaying the following: \n1) Coin name \n2) Bid price \n3) Ask_price \n4) Percentage difference between the prices')
        for a in alternate_coins:

            '''Create a symbol where the base is coin from alternate coin list and the quote is the original quote.'''

            temp = a + '/' + quote_curr

            '''Check if the symbol is supported by both the exchanges.'''
            if ((temp in b_sym) and (temp in s_sym)):
                b_ob = b.fetch_order_book(temp)['bids']
                b_pr = b_ob[0][0]
                s_ob = s.fetch_order_book(temp)['asks']
                s_pr = s_ob[0][0]
                l = [b_pr, s_pr]
                diff = abs(b_pr - s_pr) / min(l)
                print('\ncoin: ' + temp)
                '''
                print('\nb_ob: \n\n')
                print(b_ob)
                print('\ns_ob: \n\n')
                print(s_ob)
                '''
                print('\nbid_pr: ' + str(b_pr))
                print('\nask_pr: ' + str(s_pr))
                print('\npercent difference: ' + str(diff * 100))
                if min(l) < 100:
                    if diff < 0.05:
                        refund_symbol = temp
                        break
                    else:
                        refund_symbol = False
                if min(l) >= 100 and min(l) < 500:
                    if diff < 0.01:
                        refund_symbol = temp
                        break
                    else:
                        refund_symbol = False
                elif min(l) >= 500:
                    if diff < 0.001:
                        refund_symbol = temp
                        break
                    else:
                        refund_symbol = False
                time.sleep(0.5)
        else:
            refund_symbol = False

    return refund_symbol


def calculate_profit(b_ex, s_ex, b_id, s_id, amount):
    b = getattr(ccxt, b_ex)(accounts[b_ex])
    s = getattr(ccxt, s_ex)(accounts[s_ex])
    b.load_markets()
    s.load_markets()

    if ('rate' in b.fetchOrder(b_id)) and ('rate' in s.fetchOrder(s_id)):
        b_rate = b.fetchOrder(b_id)['fee']['rate']
        s_rate = s.fetchOrder(s_id)['fee']['rate']

    b_price = b.fetchOrder(b_id)['price']
    s_price = s.fetchOrder(s_id)['price']

    profit = (s_price * amount) * (1 - s_rate) - (b_price * amount) * (1 + b_rate)
    return profit


def main():
    '''main function to run with the calls'''
    '''Define a function to initialise the order ids and exchange names to some value at the
    start of the first arbitrage to make sure that arbitrage is started for the first time without
    checking for the previous arbitrage!'''

    # print(check_balance(accounts,'bitstamp', 'BTC'))
    # initialize()
    ask_market, bid_market, ask_price, bid_price, flag, refund_symbol = identify_arbitrage('LTC/USD', exchanges)
    profit = buy_sell(accounts, ask_market, bid_market, ask_price, bid_price, 'LTC/USD', 0.1, flag, refund_symbol)
    print(str(profit))


if __name__ == '__main__':
    main()