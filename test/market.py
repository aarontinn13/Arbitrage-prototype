# Market class

import ccxt
import time
import pandas
from .technicalindicators import moving_average, average_true_range, average_directional_movement_index


class Market:

    def __init__(self, exchange_id, symbol, **config):
        assert exchange_id in ccxt.exchanges
        ccxt_exchange = getattr(ccxt, exchange_id)({
            "enableRateLimit": True
        })
        ccxt_exchange.load_markets()
        assert symbol in ccxt_exchange.symbols
        assert ccxt_exchange.has["fetchOHLCV"]

        self.exchange_id = exchange_id
        self.symbol = symbol
        self.ccxt_exchange = ccxt_exchange

        self.ccxt_exchange.nonce = time.time

        self.close = 0
        self.prev_close = 0

        self.success = 0
        self.loss = 0
        self.profit = []

        self.ohlcv_timeframe = config.get("ohlcv_timeframe", "1m")

        self.sma_periods = config.get("sma_periods", 20)
        self.atr_periods = config.get("atr_periods", 15)
        self.adx_periods = config.get("adx_periods", 10)

        self.sma_value = 0
        self.atr_value = 0
        self.adx_value = 0

        self.sma_prev_value = 0
        self.atr_prev_value = 0
        self.adx_prev_value = 0

    # --------------------------------------------------------------------------

    def get_indicator_value(self, indicator, update=False):
        if update: self.update()
        if indicator == "sma":
            return self.sma_value
        elif indicator == "atr":
            return self.atr_value
        elif indicator == "adx":
            return self.adx_value
        else:
            raise ValueError("Invalid indicator: {}".format(indicator))

    def get_indicator_prev_value(self, indicator, update=False):
        if update: self.update()
        if indicator == "sma":
            return self.sma_prev_value
        # elif indicator == "atr": return self.atr_prev_value
        # elif inciator == "adx": return self.adx_prev_value
        else:
            raise ValueError("Invalid indicator: {}".format(indicator))

    def increment_success(self):
        self.success += 1

    def increment_loss(self):
        self.loss += 1

    def get_success(self):
        return self.success

    def get_loss(self):
        return self.loss

    def append_profit(self, profit):
        self.profit.append(profit)

    def get_profit(self):
        return self.profit

    # --------------------------------------------------------------------------

    def update(self):
        ccxt_exchange = self.get_ccxt_exchange()
        symbol = self.get_symbol()
        candles = ccxt_exchange.fetch_ohlcv(symbol, self.ohlcv_timeframe)
        if len(candles) > 0:
            candles_df = pandas.DataFrame([{
                "Open": c[0],
                "High": c[1],
                "Low": c[2],
                "Close": c[3],
                "Volume": c[4]
            } for c in candles])

            # TODO: make periods configurable
            sma = moving_average(candles_df, 20)
            atr = average_true_range(candles_df, 15)
            adx = average_directional_movement_index(candles_df, 10, 10)

            self.sma_prev_value = self.sma_value
            self.atr_prev_value = self.atr_value
            self.adx_prev_value = self.adx_value

            self.sma_value = sma[sma.size - 1]
            self.atr_value = atr[atr.size - 1]
            self.adx_value = adx[adx.size - 1]

            self.prev_close = self.close
            self.close = candles[-1][3]

        # TODO: modify so we don't have to use ALL candles EVERY update

    # --------------------------------------------------------------------------

    def get_close(self):
        return self.close

    def get_prev_close(self):
        return self.prev_close

    def get_exchange_id(self):
        return self.exchange_id

    def get_symbol(self):
        return self.symbol

    def get_ccxt_exchange(self):
        return self.ccxt_exchange

    def get_base_currency(self):
        symbol = self.get_symbol()
        return symbol.split("/")[0]

    def get_quote_currency(self):
        symbol = self.get_symbol()
        return symbol.split("/")[1]