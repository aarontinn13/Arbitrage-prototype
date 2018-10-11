# Manager class
# test

import time
import ccxt
import json
from .market import Market
from .account import Account

class Manager:

	def __init__(self, init_accounts=[], config=None):
		self.markets = dict()
		self.accounts = dict()
		self.exchange_ids = []

		#self.profit_arr = dict() # map market tuple to list
		self.kelly = dict() # map symbols to kelly

		self.loop_period = 20 # loop period in seconds
		self.loop_count = 0
		self.min_loop_count = 2 # the minimum loop number to start trading

		self.max_positions = 1 # max positions per account symbol
		self.trend_strength = 25 # TODO make this some config option
		self.account_risk_coeff = 0.025
		self.fee_rate = 0.0025
		self.kelly_file_name = "kelly.json"

		# add initial accounts
		for a in init_accounts:
			if "disabled" not in a or not a["disabled"]:
				self.add_account(a)

	# Add account to manager given an account_info dict
	def add_account(self, account_info):
		assert "exchange_id" in account_info
		assert "symbols" in account_info and isinstance(account_info["symbols"], list)

		# build and add Account instance to manager
		exchange_id = account_info["exchange_id"]
		symbols = account_info["symbols"]
		markets = [self.get_market(exchange_id, s) for s in symbols]
		account = Account(exchange_id, markets, account_info)
		self.accounts[account.id] = account

		print("Added account for {0} with {1} symbols".format(exchange_id, len(symbols)))

		# add exchange ID if not added already
		if exchange_id not in self.exchange_ids: self.exchange_ids.append(exchange_id)

	# --------------------------------------------------------------------------

	# Start manager loop
	def start(self):
		print("Manager started at {}".format(time.time()))
		self.load_kelly(self.kelly_file_name)

		# TODO: improve this loop's efficiency
		while True:
			self.loop_count += 1
			print("Current loop: {}".format(self.loop_count))
			for exchange_id in self.exchange_ids:
				for account in self.get_accounts_iter(exchange_id):
					try:
						account.update()
					except Exception as err:
						print("Excepted account update error: {}".format(err))
					account.print_account_value()
					for symbol in account.get_symbols_iter():
						try:
							self.process_symbol(account, symbol)
						except Exception as err:
							pass
							print("Excepted error in loop at {1}-{2}: {0}".format(err, exchange_id, symbol))
			self.save_kelly(self.kelly_file_name)
			time.sleep(self.loop_period)

	# Process a single symbol in some account
	def process_symbol(self, account, symbol):
		#print("Processing {0}-{1} in account {2}".format(account.get_exchange_id(), symbol, account.get_id()))
		print("{}-{}-{}: balance (b/q): ({}/{})".format(account.get_exchange_id(), symbol, account.get_id(), account.get_base_balance(symbol), account.get_quote_balance(symbol)))

		exchange_id = account.get_exchange_id()
		market = self.get_market(exchange_id, symbol)
		market.update()

		close = market.get_close()
		prev_close = market.get_prev_close()
		sma_value = market.get_indicator_value("sma")
		sma_prev_value = market.get_indicator_prev_value("sma")
		adx_value = market.get_indicator_value("adx")

		# try to close positions
		for position_id, position in account.get_positions_iter(symbol = symbol):
			position.update()
			status = position.get_status()
			now = time.time()

			if status == "open-pending":
				open_ts = position.get_open_ts()
				diff = now - open_ts
				if diff > 60:
					self.cancel_position(account, position_id)

			elif status == "close-pending":
				close_ts = position.get_close_ts()
				diff = now - close_ts
				if diff > 60:
					self.cancel_position(account, position_id)

			elif status == "opened":
				side = position.get_side()
				price = position.get_price()
				stop_loss_price = position.get_stop_loss_price()

				#print("Try to close position in {}-{}".format(account.get_exchange_id(), position.get_symbol()))

				if side == "buy":
					if close < sma_value and close > price:
						self.close_position(account, position_id, close)
						market.increment_success()
					elif close < stop_loss_price:
						print("close stop loss")
						self.close_position(account, position_id, stop_loss_price)
						market.increment_loss()
				elif side == "sell":
					if close > sma_value and close < price:
						self.close_position(account, position_id, close)
						market.increment_success()
					elif close > stop_loss_price:
						print("close stop loss")
						self.close_position(account, position_id, stop_loss_price)
						market.increment_loss()

		# try to open position
		num_positions = sum(1 for x in account.get_positions_iter(symbol = symbol))
		if self.loop_count >= self.min_loop_count and num_positions < self.max_positions:
			if prev_close < sma_prev_value and close > sma_value: # and adx_value > self.trend_strength:
				self.open_position(account, symbol, "buy", close)
			elif prev_close > sma_prev_value and close < sma_value:
				self.open_position(account, symbol, "sell", close)
			else:
				pass # DO NOTHING

	def open_position(self, account, symbol, side, price):
		#print("Open {0} position for {1}-{2} at {3}".format(side, account.get_exchange_id(), symbol, price))

		market = account.get_market(symbol)
		atr_value = market.get_indicator_value("atr")

		slp = self.get_stop_loss_price(side, price, atr_value)
		amount = self.get_position_size(account, market, side, slp)

		return account.open_position(symbol, side, amount, price, slp)

	def close_position(self, account, position_id, price):
		#print("Close position")

		position = account.close_position(position_id, price)
		market = position.get_market()

		side = position.get_side()
		amount = position.get_amount()
		orig_price = position.get_price()

		if side == "buy":
			profit = amount * (price - orig_price)
			market.append_profit(profit)
		elif side == "sell":
			profit = amount * (orig_price - price)
			market.append_profit(profit)

		# TODO: handle closing this position, deleting it or whatever

	def cancel_position(self, account, position_id):
		return account.cancel_position(position_id)

	def get_stop_loss_price(self, side, price, atr_value):
		if side == "buy":
			return price - 2 * atr_value
		elif side == "sell":
			return price + 2 * atr_value
		else:
			raise ValueError("Invalid side: {}".format(side))

	def get_position_size(self, account, market, side, stop_loss_price):
		exchange_id = market.get_exchange_id()
		symbol = market.get_symbol()
		market_id = (exchange_id, symbol)

		if symbol not in self.kelly:
			self.kelly[symbol] = 0.25

		profit_arr = market.get_profit()
		kelly = self.kelly[symbol]

		# learning step
		if len(profit_arr) > 1:

			# probability of success
			success = market.get_success()
			loss = market.get_loss()
			w = success/(success + loss)

			# divide profit into positive and negative
			positive = [x for x in profit_arr if x >= 0]
			negative = [-x for x in profit_arr if x < 0]

			if len(positive) > 0 and len(negative) > 0:

				pos_avg = sum(positive) / len(positive)
				neg_avg = sum(negative) / len(negative)

				r = pos_avg / neg_avg
				kelly = abs((w - (1-w)/r)/2)
				self.kelly[symbol] = kelly

				print("Updated kelly for symbol {0} to {1}".format(symbol, kelly))

		# calculation step
		trade_risk = 0
		trade_risk_coeff = 0
		close = market.get_close()

		if close < stop_loss_price:
			trade_risk = 1 - close/stop_loss_price
		else:
			trade_risk = 1 - stop_loss_price/close
		# trade_risk = max(1 - stop_loss_price/close)

		if trade_risk > self.account_risk_coeff:
			trade_risk_coeff = (self.account_risk_coeff/trade_risk)
		else:
			trade_risk_coeff = (trade_risk/self.account_risk_coeff)

		balance = 0
		if side == "buy":
			balance = account.get_quote_balance(symbol) / (1 + self.fee_rate) / close
		elif side == "sell":
			balance = account.get_base_balance(symbol)

		coeff = min(kelly, trade_risk_coeff, 1) # TODO: make this a "max spend rate" constant
		size = balance * coeff

		# here we bound the size based on what the minimums for CCXT are
		ccxt_exchange = market.get_ccxt_exchange()
		market = ccxt_exchange.market(symbol)

		amount_min = market["limits"]["amount"]["min"]
		cost_min = market["limits"]["cost"]["min"]
		amount_min_notional = cost_min / close

		return max(size, amount_min, amount_min_notional)

	# load kelly to file
	def load_kelly(self, file_name):
		with open(file_name, 'r') as f:
			self.kelly = json.load(f)

	# save kelly from file
	def save_kelly(self, file_name):
		with open(file_name, 'w') as f:
			json.dump(self.kelly, f)

	# --------------------------------------------------------------------------

	# Return generator over accounts with matching exchange ID
	# If exchange_id == None, returns generator over all accounts
	def get_accounts_iter(self, exchange_id = None):
		for account in self.accounts.values():
			if exchange_id is None or account.get_exchange_id() == exchange_id:
				yield account

	# Return Market instance given exchange ID and symbol
	# By default creates the Market instance if it doesn't exist
	def get_market(self, exchange_id, symbol, create = True):
		key = (exchange_id, symbol)
		if key in self.markets:
			return self.markets[key]
		elif create:
			market = Market(exchange_id, symbol)
			self.markets[key] = market
		return market