"""An Interface for bitcoin api
Using Factory design pattern to accept to different api address

#DOTO: rule the history format
"""

import json
import re
from util import call_api


class BlockChainInfoAPI():
    """Implemnt blockchain version of bitcoin api
    interface
    """
    def __init__(self):
        self._base_url = 'https://blockchain.info/'

    def pushtx(self, tx):
        """push the transaction
        """
        if not re.match('^[0-9a-fA-F]*$', tx):
            tx = tx.encode('hex')
        return call_api(self._base_url, 'pushtx', {'tx': tx})

    def unspent(self, addr):
        """to get unspen of the address
        """
        result = []

        try:
            data = call_api(self._base_url, 'unspent?address='+addr)
        except Exception as e:
            if str(e) == 'No free outputs to spend':
                pass
            else:
                raise Exception(e)

        try:
            jsonobj = json.loads(data)
            for o in jsonobj['unspent_outputs']:
                # to get tx_hash big endian
                h = o['tx_hash_big_endian']
                #h = obj['tx_hash'].decode('hex')[::-1].encode('hex')
                result.append({
                    "output": h+':'+str(o['tx_output_n']),
                    "value": o['value']
                })
        except:
            raise Exception("Failed to decode data: "+data)

        return result

    def get_tx_confirmation(self, tx):
        """In block chain info, there is no api to
        get transaction confirmation
        """
        block_count = call_api(self._base_url, 'q/getblockcount')

        source = 'tx/{}?show_adv=false&format=json'.format(tx)
        data = call_api(self._base_url, source)

        try:
            jsonobj = json.loads(data)
        except:
            raise Exception("Failed to decode data: "+data)

        block_height = jsonobj['block_height']

        return int(block_count) - int(block_height) + 1

    def history(self, addr):
        """call pybitcointool history function
        to get the result
        """
        txs = []
        offset = 0
        while 1:
            source = 'address/%s?format=json&offset=%s' % (addr, offset)
            data = call_api(self._base_url, source)

            try:
                jsonobj = json.loads(data)
            except:
                raise Exception("Failed to decode data: "+data)

            txs.extend(jsonobj["txs"])
            if len(jsonobj["txs"]) < 50:
                break
            offset += 50
            # TODO: Record this message to logger
            #print("Fetching more transactions... "+str(offset)+'\n')

        outs = {}
        for tx in txs:
            for o in tx["out"]:
                if o['addr'] == addr:
                    key = str(tx["tx_index"])+':'+str(o["n"])
                    outs[key] = {
                        "address": o["addr"],
                        "value": o["value"],
                        "output": tx["hash"]+':'+str(o["n"]),
                        "time": tx["time"],
                        "block_height": tx.get("block_height", None)
                    }

        for tx in txs:
            for i, inp in enumerate(tx["inputs"]):
                if inp["prev_out"]["addr"] == addr:
                    key = str(inp["prev_out"]["tx_index"]) + \
                        ':'+str(inp["prev_out"]["n"])
                    if outs.get(key):
                        outs[key]["spend"] = tx["hash"]+':'+str(i)

        return [outs[k] for k in outs]

    def balance(self, address):
        """get the balance of the address in BTC
        """
        data = self.unspent(address)
        value = 0.0

        for o in data:
            value += o['value']

        return value

    def currencyRate(self, currencyType):
        """use bitcoin api rate
        give the param currency_type to get
        correspond value
        """
        data = call_api(self._base_url, 'ticker')

        try:
            jsonobj = json.loads(data)
        except:
            raise Exception('Failed to decode data: '+data)

        try:
            rate = jsonobj[currencyType]
        except:
            raise Exception('unsupported currency')

        return rate['last']
