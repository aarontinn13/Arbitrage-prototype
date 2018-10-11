import ccxt #imports the whole library

bitstamp = getattr(ccxt,'bitstamp') #create the class from the bitstamp module


#print(bit)

bit = bitstamp({'uid': 'kwsm6715',
                'api_key': 'UVY4L0wBzqDqp3agiY3ThVadrrLGHfUH',
                'secret': '7MjcWmDwCi4YpiugvmXe94p5TPGK7F1M',
                })
#print(bit)


bit.load_markets()




yobit = getattr(ccxt,'livecoin')

yo = yobit({'uid': 'noah13nelson@gmail.com',

                            'api_key': 'YgpVDcsqSdar2YnNyzWhAzxraT2gcHFN',

                            'secret': 't9xm2v8yrhYbfwxMBbQ49huTSDFPBxP3' ,

            })

yo.load_markets()


a = yo.fetch_deposit_address('LTC')

add = a['address']

tag = a['tag']

print(a)

print(bit.withdraw('LTC',0.1,add))

print(yo.fetch_balance()['info'])
