# -*- coding: utf-8 -*-
from api_manager import APIFactory
from btcNode import BlockChainInfoAPI
from bitcoin import main as BtcTools
from bitcoin import transaction as BtcTrans
from bitcoin import stealth as BtcStealth


class ApiFacade(object):

    """this class's function is to handle all api
    and to check whether api work or not. it will
    choose the one worked if other api is dead.
    """

    def __init__(self):
        """give the priority for part of apis
        """
        self.btcNode = BlockChainInfoAPI()
        self._api_priority = [
            'InsightAPI',
            'BlockrAPI',
            'BlockChainInfoAPI']

    def __log(self, msg):
        print msg

    def callApi(self, funcName, *args):
        try:
            result = getattr(self.btcNode, funcName)(*args)
            return result
        except Exception as e:
            print(e)

    def try_api_loop(self, func_name, *args):
        """encapsulate for dynamic call
        api function
        """
        for api_name in self._api_priority:
            try:
                api = APIFactory.get_class(api_name)()
                # to get instance of api class
                result = getattr(api, func_name)(*args)
                return result
            except Exception as e:
                print(e)
                print('---try to use another api---')
                continue

    def sendTx(self, tx):
        return self.callApi('pushtx', tx)

    def history(self, address):
        return self.callApi('history', address)

    def unspent(self, address):
        return self.callApi('unspent', address)

    def finalBalance(self, address):
        return self.callApi('balance', address)

    def get_tx_confirmation(self, tx):
        return self.callApi('get_tx_confirmation', tx)

    def createPrivateKey(self, passphrase=''):
        priKey = BtcTools.random_key()
        if passphrase:
            priKey = BtcTools.sha256(passphrase)

        return BtcTools.encode_privkey(priKey, 'wif_compressed')

    def createPublicKey(self, privateKey):
        return BtcTools.privtopub(privateKey)

    def createAddress(self, publicKey):
        return BtcTools.pubtoaddr(publicKey)

    def createAddressByScript(self, script):
        return BtcTrans.scriptaddr(script)

    def createMultisig(self, publicKeys, *args):
        return BtcTrans.mk_multisig_script(publicKeys, *args)

    def createTx(self, txIn, txOut):
        return BtcTrans.mktx(txIn, txOut)

    def encodePrivateKey(self, privateKey, format):
        return BtcTools.encode_privkey(privateKey, format)

    def getPrivateKeyFormat(self, privateKey):
        return BtcTools.get_privkey_format(privateKey)

    def getPublicKeyFormat(self, privateKey):
        return BtcTools.get_pubkey_format(privateKey)

    def singleSign(self, tx, i, privateKey):
        return BtcTrans.sign(tx, i, privateKey)

    def multiSign(self, tx, i, script, privateKey):
        return BtcTrans.multisign(tx, i, script, privateKey)

    def applyMultiSign(self, tx, i, script, sig1, sig2, sig3):
        return BtcTrans.apply_multisignatures(tx, 0, script, sig1, sig2, sig3)

    def calcBalance(self, unspent):
        balance = 0
        for u in unspent:
            balance += u['value']
        return balance

    def singleSignTxInOut(self, srcAddr, dstAddr, amount, txFee):
        unspentOuts = self.unspent(srcAddr)
        # 選擇指定地址中，所有可以湊足付出金額的bitcoin數組，由大到小
        txIns = BtcTrans.select(unspentOuts, amount + txFee)
        totalBalance = self.calcBalance(txIns)
        changeval = totalBalance - amount - txFee

        if dstAddr[0] == 'v' or dstAddr[0] == 'w':
            # stealth
            ephemPrivkey = BtcTools.random_key()
            nonce = int(BtcTools.random_key()[:8], 16)
            if dstAddr[0] == 'v':
                # network = 'btc'
                raise Exception(
                    'Stealth address payments only supported on testnet at this time.')
            else:
                network = 'testnet'

            txOuts = BtcStealth.mk_stealth_tx_outputs(
                dstAddr, amount, ephemPrivkey, nonce, network)
        else:
            txOuts = [{'value': amount, 'address': dstAddr}]

        if changeval > 0:
            # 找零要還給來源地址，剩餘金額 = 支付金額 - 扣除金額
            txOuts.append({'value': changeval, 'address': srcAddr})

        return txIns, txOuts

    def multiSignTxInOut(self, srcAddr, dstAddr, amount, txFee):
        txIns = self.history(srcAddr)
        txOuts = [{'value': amount, 'address': dstAddr}]
        return txIns, txOuts