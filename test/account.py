# Account class

import ccxt
import time
from itertools import count
from .position import Position, SimulatedPosition
from .market import Market


class Account:

	id_generator = count()

	def __init__(self, exchange_id, markets, config):
		# TODO: validation

		self.id = Account.id_generator.__next__()
		self.exchange_id = exchange_id
		self.markets = dict()
		self.symbols = []
		self.positions = dict()
		self.balance = dict() # map currency name to balance

		self.user_id = config.get("user_id", None)
		self.api_key = config.get("api_key", None)
		self.secret = config.get("secret", None)

		self.ccxt_exchange = getattr(ccxt, exchange_id)({
			"recvWindow": 10000000,
			"options": {
				"adjustForTimeDifference": True
			},
			"enableRateLimit": True,
			"uid": self.user_id,
			"apiKey": self.api_key,
			"secret": self.secret
		})

		# add markets
		for m in markets:
			self.add_market(m)

	# do this every loop
	def load_time_difference(self):
		exchange = self.get_ccxt_exchange()
		our_time = exchange.milliseconds()
		their_time = exchange.publicGetTime()["serverTime"]
		self.time_difference = their_time - our_time

	# add a market to this account
	def add_market(self, market):
		if isinstance(market, Market):
			symbol = market.get_symbol()
			base = symbol.split("/")[0]
			quote = symbol.split("/")[1]
			self.markets[symbol] = market
			self.symbols.append(symbol)
			self.balance[base] = 0
			self.balance[quote] = 0
		else:
			print("Markets must be instances of tradebot.Market")
			# TODO: change this message to a logging call

	def print_account_value(self):
		quotes = dict()
		for symbol in self.symbols:
			quote_cur = symbol.split("/")[1]
			if quote_cur not in quotes:
				quotes[quote_cur] = 0
			market = self.get_market(symbol)
			base_balance = self.get_base_balance(symbol)
			close = market.get_close()
			quotes[quote_cur] += close * base_balance
		for quote in quotes:
			quotes[quote] += self.get_balance(quote)
		print(quotes)


	# --------------------------------------------------------------------------

	def open_position(self, symbol, side, amount, price, stop_loss_price):
		position = Position(self, symbol)

		base_change = 0
		quote_change = 0

		(base_change, quote_change) = position.open(side, amount, price, stop_loss_price)

		# update balance
		market = position.get_market()
		base_currency = market.get_base_currency()
		quote_currency = market.get_quote_currency()
		self.balance[base_currency] += base_change
		self.balance[quote_currency] += quote_change

		# add position
		position_id = position.get_id()
		self.positions[position_id] = position

		print("Opened {} position on {}-{} for {} at {}".format(side, self.get_exchange_id(), symbol, amount, price))

		return position

	def close_position(self, position_id, price):
		position = self.get_position(position_id)

		base_change = 0
		quote_change = 0

		try:
			(base_change, quote_change) = position.close(price)
		except Exception as err:
			print("excepted error: {}".format(err))

		# update balance
		market = position.get_market()
		base_currency = market.get_base_currency()
		quote_currency = market.get_quote_currency()
		self.balance[base_currency] += base_change
		self.balance[quote_currency] += quote_change

		print("Closed {} position on {}-{} for {} at {}".format(position.get_side(), self.get_exchange_id(), position.get_symbol(), position.get_amount(), price))

		return position

		# we don't remove the position becasue its not closed, but close-pending
		# we remove it in the update call, removing all closed positions

	def cancel_position(self, position_id):
		position = self.get_position(position_id)
		position.cancel()
		self.positions.pop(position_id)

	def update(self):
		ccxt_exchange = self.get_ccxt_exchange()
		balance_info = ccxt_exchange.fetch_balance()
		#self.load_time_difference()
		for currency in self.balance:
			if currency in balance_info:
				self.balance[currency] = balance_info[currency]["free"]

	# --------------------------------------------------------------------------

	def get_id(self):
		return self.id

	def get_exchange_id(self):
		return self.exchange_id

	def get_ccxt_exchange(self):
		return self.ccxt_exchange

	def get_market(self, symbol):
		return self.markets[symbol]

	def get_balance(self, currency):
		return self.balance[currency]

	def get_base_balance(self, symbol):
		currency = symbol.split("/")[0]
		return self.get_balance(currency)

	def get_quote_balance(self, symbol):
		currency = symbol.split("/")[1]
		return self.get_balance(currency)

	def get_position(self, position_id):
		return self.positions[position_id]

	def get_symbols_iter(self):
		for s in self.symbols:
			yield s

	def get_positions_iter(self, symbol = None, status = None):
		for i, p in self.positions.items():
			if symbol is not None and p.get_symbol() != symbol:continue
			if status is not None and p.get_status() != status:continue
			yield i, p