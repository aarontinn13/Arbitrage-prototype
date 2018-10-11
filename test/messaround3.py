import ccxt

bitstamp = ccxt.bitstamp

bitstamp = bitstamp({'uid': 'kwsm6715',
                    'api_key': 'eFrPYCe3KJ2w6aKb6eUYwvBqjdVnkmoU',
                    'secret': '6xc0U55xj4pHJtQDRntzIobGfcoLDlfJ',
                    })

bitstamp.load_markets()

print('bitstamp LTC balance:', bitstamp.fetch_balance()['info']['ltc_available'])

poloniex = ccxt.poloniex

poloniex = poloniex({'uid': 'noah13nelson@gmail.com',
                    'api_key': 'JHGCEVR5-VOLY72AW-ZTDH2DXP-S14TO6KY',
                    'secret': '93475ba24b1a371bbbc07937cfdb5da3f284f389039afba9f90fe208634ff5a6faaedd79e9b2ff14cb937c0c7f9984ee1ce038827038c7dc6447359bead24b8b',
                    })

poloniex.load_markets()


print('poloniex LTC balance:',poloniex.fetch_balance()['info']['LTC']['available'])