# Position class

from itertools import count
import time

class Position:

	id_generator = count()

	FEE_RATE = 0.0025 # TODO: improve fee determination

	def __init__(self, account, symbol, **config):
		# TODO: validation

		self.id = Position.id_generator.__next__()
		self.account = account
		self.symbol = symbol

		self.status = "unopened"
		self.order_id = ""

		self.open_ts = 0
		self.close_ts = 0
		self.cancel_ts = 0

		self.side = ""
		self.amount = 0
		self.price = 0
		self.close_price = 0
		self.close_amount = 0
		self.open_sell_revenue = 0
		self.stop_loss_price = 0

	# --------------------------------------------------------------------------

	def open(self, side, amount, price, stop_loss_price):
		if self.get_status(update = True) == "unopened":
			self.status = "open-pending"
			self.open_ts = time.time()

			ccxt_exchange = self.get_ccxt_exchange()
			ccxt_market = ccxt_exchange.market(self.get_symbol())

			amount_prec = ccxt_market["precision"]["amount"]
			price_prec = ccxt_market["precision"]["price"]

			self.side = side
			self.amount = round(amount, amount_prec)
			self.price = round(price, price_prec)
			self.stop_loss_price = round(stop_loss_price, price_prec)

			#print("Try open {} {}-{} at {}".format(self.side, self.get_exchange_id(), self.get_symbol(), self.price))

			fee = round(amount * price * Position.FEE_RATE, price_prec)
			base_change = 0
			quote_change = 0

			if side == "buy":
				response = ccxt_exchange.create_limit_buy_order(self.get_symbol(), self.amount, self.price)
				self.order_id = response["id"]
				base_change = amount
				quote_change = -amount*price - fee
			elif side == "sell":
				response = ccxt_exchange.create_limit_sell_order(self.get_symbol(), self.amount, self.price)
				self.order_id = response["id"]
				base_change = -amount
				quote_change = amount*price - fee
				self.open_sell_revenue = quote_change

			self.status = "open-pending"

			return (base_change, quote_change)

		else:
			raise RuntimeError("Attempt to open non-unopened position")

	def close(self, price):
		if self.get_status(update = True) == "opened":
			self.status = "close-pending"
			self.close_ts = time.time()

			ccxt_exchange = self.get_ccxt_exchange()
			ccxt_market = ccxt_exchange.market(self.get_symbol())

			amount_prec = ccxt_market["precision"]["amount"]
			price_prec = ccxt_market["precision"]["price"]

			self.close_price = round(price, price_prec)

			#print("Try close {2} {0}-{1} at {3}".format(self.get_exchange_id(), self.get_symbol(), self.side, self.close_price))

			# estimate the amount of coin to buy in the case of side == "sell"
			fee = round(self.amount * price * Position.FEE_RATE, price_prec)
			self.close_amount = round((self.open_sell_revenue - fee) / price, amount_prec)

			base_change = 0
			quote_change = 0

			# NOTE: the different sides use different trade amounts
			if self.side == "buy":
				response = ccxt_exchange.create_limit_sell_order(self.get_symbol(), self.amount, self.close_price)
				self.order_id = response["id"]
				base_change = -self.amount
				quote_change = self.amount*price - fee
			elif self.side == "sell":
				response = ccxt_exchange.create_limit_buy_order(self.get_symbol(), self.close_amount, self.close_price)
				self.order_id = response["id"]
				base_change = (self.open_sell_revenue - fee) / price
				quote_change = -self.open_sell_revenue

			self.status = "close-pending"

			return (base_change, quote_change)

		else:
			raise RuntimeError("Attempt to close non-opened position")

	def cancel(self):
		status = self.get_status()
		if status == "open-pending" or status == "close-pending":
			self.cancel_ts = time.time()

			ccxt_exchange = self.get_ccxt_exchange()
			order_id = self.get_order_id()
			symbol = self.get_symbol()
			ccxt_exchange.cancel_order(order_id, symbol)
			# TODO
		else:
			raise RuntimeError("Attempt to cancel non-pending position")


	# Update the position status
	# TODO: handle errors appropriately, log warnings but let program continue
	def update(self):
		status = self.get_status(update = False)
		if status == "open-pending" or status == "close-pending":
			ccxt_exchange = self.get_ccxt_exchange()
			order_id = self.get_order_id()
			order = ccxt_exchange.fetch_order(order_id, self.get_symbol())
			order_status = order["status"]

			if order_status == "closed":
				if status == "open-pending": self.status = "opened"
				elif status == "close-pending": self.status = "closed"
			elif order_status == "canceled":
				if status == "open-pending": self.status = "unopened"
				elif status == "close-pending": self.status = "opened"

	# --------------------------------------------------------------------------

	def get_id(self):
		return self.id

	def get_account(self):
		return self.account

	def get_symbol(self):
		return self.symbol

	def get_market(self):
		account = self.get_account()
		symbol = self.get_symbol()
		return account.get_market(symbol)

	def get_exchange_id(self):
		return self.get_account().get_exchange_id()

	def get_ccxt_exchange(self):
		return self.get_account().get_ccxt_exchange()

	def get_order_id(self):
		return self.order_id

	def get_status(self, update = False):
		if update: self.update()
		return self.status

	def get_side(self):
		return self.side

	def get_amount(self):
		return self.amount

	def get_price(self):
		return self.price

	def get_stop_loss_price(self):
		return self.stop_loss_price

	def get_open_ts(self):
		return self.open_ts

	def get_close_ts(self):
		return self.close_ts


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class SimulatedPosition(Position):

	def open(self, side, amount, price, stop_loss_price):
		if self.get_status() == "unopened":
			self.status = "open-pending"
			self.open_ts = time.time()

			self.side = side
			self.amount = round(amount, 8)
			self.price = round(price, 2)
			self.stop_loss_price = round(stop_loss_price, 2)

			fee = round(amount * price * Position.FEE_RATE, 2)
			base_change = 0
			quote_change = 0

			# TODO: change rounding to be based on CCXT precisions

			if side == "buy":
				base_change = amount
				quote_change = -amount*price - fee
			elif side == "sell":
				base_change = -amount
				quote_change = amount*price - fee
				self.open_sell_revenue = quote_change

			self.status = "opened"

			return (base_change, quote_change)
		else:
			raise RuntimeError("Attempt to open non-unopened position")

	def close(self, price):
		if self.get_status() == "opened":
			self.status = "close-pending"
			self.close_ts = time.time()

			self.close_price = price

			fee = round(self.amount * price * Position.FEE_RATE, 2)
			base_change = 0
			quote_change = 0

			# TODO: change rounding to be based on CCXT precisions

			if self.side == "buy":
				base_change = -self.amount
				quote_change = self.amount*price - fee
			elif self.side == "sell":
				base_change = (self.open_sell_revenue - fee) / price
				quote_change = -self.open_sell_revenue

			self.status = "closed"

			return (base_change, quote_change)
		else:
			raise RuntimeError("Attempt to close non-opened position")

	def cancel(self):
		status = self.get_status()
		if status == "open-pending" or status == "close-pending":
			self.cancel_ts = time.time()
		else:
			raise RuntimeError("Attempt to cancel non-pending position")

	def update(self):
		pass # do nothing on update