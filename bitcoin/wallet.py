# -*- coding: utf-8 -*-
from api_facade import ApiFacade


class Wallet(object):

    '''a simple wallet for handling *one* private key and contain some function
    like a real world wallet. Furthermore, this can create a sigle key address or multi-sig
    address wallet.

    There are three ways to create your wallet.
    1. createWallet
    2. import_privatekey
    3. createMultisigWallet

    1 and 2 are for single key
    3 for multi-sig use

    '''

    def __init__(self):
        self.api = ApiFacade()
        self.priKey = ''
        self.pubKey = ''
        self.address = ''
        self.script = ''

    def createMultisigWallet(self):
        '''randomly create 4 priv key, and rule a 3 of 4 address
        # NOTE: situation is still not confirm..
        '''
        prikeys = [self.api.createPrivateKey() for i in range(4)]
        pubkeys = [self.api.createPublicKey(key) for key in prikeys]
        self.priKey = prikeys
        self.pubKey = pubkeys
        self.script = self.api.createMultisig(pubkeys, 3, 4)
        self.address = self.api.createAddressByScript(self.script)

    def createWallet(self, passphrase=''):
        if passphrase:
            self.priKey = self.api.createPrivateKey(passphrase)
        else:
            self.priKey = self.api.createPrivateKey()

        self.pubKey = self.api.createPublicKey(self.priKey)
        self.address = self.api.createAddress(self.pubKey)

    def importPrivateKey(self, privatekey):
        # TODO:目前先統一使用 wif compressed 格式匯出匯入，未來可以擴充轉換
        fmt = self.api.getPrivateKeyFormat(privatekey)
        if 'wif_compressed' != fmt:
            return 'Error: This is %s type. Must be wif_compressed type.' % fmt

        self.priKey = privatekey
        self.pubKey = self.api.createPublicKey(self.priKey)
        self.address = self.api.createAddress(self.pubKey)

    def exportPrivateKey(self):
        return self.api.encodePrivateKey(self.priKey, 'wif_compressed')

    def finalBalance(self):
        return self.api.finalBalance(self.address)

    def history(self):
        return self.api.history(self.address)

    def sendBTC(self, dstAddr, amount, fee=10000):
        '''In order to send money, we need to get the previous transaction history
        and then make an out rule, sign the transactions

        # TODO: solve below issue
        issue: if I import the key from multi-bit, I would not to be able to pushtx
        error message is An outpoint is already spent in. how to solve this
        '''
        if self.address[:1] != '1':
            # if not 1, this address is not multi-sig addr
            # how do I apply fee here..
            tx = self.__multiSignTx(dstAddr, amount, fee)
        else:
            tx = self.__singleSignTx(dstAddr, amount, fee)

        return self.api.sendTx(tx)

    # Single-sign transaction
    def __singleSignTx(self, dstAddr, amount, txFee):
        # if self.send_amount + self.txfee > self.balance:
        #     raise LowBalanceError("Insufficient funds to send")
        priKey = self.priKey
        srcAddr = self.address

        txIns, txOuts = self.api.singleSignTxInOut(srcAddr, dstAddr, amount, txFee)

        tx = self.api.createTx(txIns, txOuts)
        for i in range(len(txIns)):
            tx = self.api.singleSign(tx, i, priKey)

        # txIns, txOuts, tx, deserialize(tx)
        self.txIns = txIns
        self.txOuts = txOuts
        self.tx = tx
        return tx

    # Multi-sign transaction
    def __multiSignTx(self, dstAddr, amount, txFee):
        priKey = self.priKey
        srcAddr = self.address
        script = self.script

        txIns, txOuts = self.api.multiSignTxInOut(srcAddr, dstAddr, amount, txFee)

        tx = self.api.createTx(txIns, txOuts)
        sig1 = self.api.multiSign(tx, 0, script, priKey[0])
        sig2 = self.api.multiSign(tx, 0, script, priKey[1])
        sig3 = self.api.multiSign(tx, 0, script, priKey[2])
        tx = self.api.applyMultiSign(tx, 0, script, sig1, sig2, sig3)
        return tx
