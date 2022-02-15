import logging
import secrets
import configparser

from eth_account import Account
from web3 import Web3


class Hunter:

    def __init__(self):
        logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s', datefmt='%H:%M:%S %p', level=logging.INFO)

        self.config = configparser.ConfigParser()

        self.config.read('conf.ini')

        self.address = Web3.toChecksumAddress(self.config['settings']['address'])

        if self.config.getboolean('settings', 'useETH'):
            self.w3eth = self.connect(self.config['provider']['eth'])

            if self.w3eth.isConnected():
                logging.info('Connected to ETH node')

        if self.config.getboolean('settings', 'useBSC'):
            self.w3bsc = self.connect(self.config['provider']['bsc'])

            if self.w3bsc.isConnected():
                logging.info('Connected to BSC node')


        if self.config.getboolean('settings', 'usePOLYGON'):
            self.w3mtc = self.connect(self.config['provider']['polygon'])

            if self.w3mtc.isConnected():
                logging.info('Connected to POLYGON node')

        logging.info('Starting to hunt a rich wallet, wish me luck...')

        self.checker()


    def checker(self):
        n = 1

        while True:
            # Generate Private Key
            private_key = '0x' + secrets.token_hex(32)

            # Get Public Key from Private Key
            public_key = Account.from_key(private_key).address

            if self.config.getboolean('settings', 'useETH'):
                try:
                    # Check balance in ETH network
                    ethBalance = self.w3eth.eth.get_balance(public_key)
                    if ethBalance:
                        logging.info('Found balance in ETH network')
                        # If balance is greater than zero, write a log
                        self.writeLog('ETH', public_key, private_key)

                        if self.config.getboolean('settings', 'sendWhenFind'):
                            self.send(self.w3eth, ethBalance, public_key, private_key)
                except Exception as e:
                    logging.exception(e)
            
            if self.config.getboolean('settings', 'useBSC'):
                try:
                    # Check balance in BSC network
                    bscBalance = self.w3bsc.eth.get_balance(public_key)
                    if bscBalance:
                        logging.info('Found balance in BSC network')
                        # If balance is greater than zero, write a log
                        self.writeLog('BSC', public_key, private_key)

                        if self.config.getboolean('settings', 'sendWhenFind'):
                            self.send(self.w3bsc, bscBalance, public_key, private_key)
                except Exception as e:
                    logging.exception(e)
            
            if self.config.getboolean('settings', 'usePOLYGON'):
                try:
                    # Check balance in POLYGON network
                    mtcBalance = self.w3mtc.eth.get_balance(public_key)
                    if mtcBalance:
                        logging.info('Found balance in POLYGON network')
                        # If balance is greater than zero, write a log
                        self.writeLog('POLYGON', public_key, private_key)

                        if self.config.getboolean('settings', 'sendWhenFind'):
                            self.send(self.w3mtc, mtcBalance, public_key, private_key)
                except Exception as e:
                    logging.exception(e)

            logging.info('Wallets checked: %s', str(n))
            n += 1


    def writeLog(network, privkey, pubkey):
        try:
            f = open('./logs/' + network + '-' + pubkey + '.txt', 'w+')
            f.write('Public key: ' + pubkey + '\n')
            f.write('Private key: ' + privkey + '\n')
            f.close()
        except Exception as e:
            logging.exception(e)


    def send(self, w3, amount, pubkey, privkey):
        txn = {
            'from': Web3.toChecksumAddress(pubkey),
            'to': Web3.toChecksumAddress(self.address),
            'gasPrice': Web3.fromWei(w3.eth.gas_price, 'gwei'),
            'gas': 250000,
            'value': amount,
            'nonce': w3.eth.get_transaction_count(pubkey)
        }

        gasEst = self.estimateGas(w3, txn)

        txn.update({ 'gas': gasEst[0], 'value': gasEst[1] })

        signed_txn = w3.eth.account.sign_transaction(txn, privkey)

        send = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        logging.info('Transaction hash: %s', send.hex())


    def estimateGas(self, w3, txn):
        gas = w3.eth.estimateGas({
            'from': txn['from'],
            'to': txn['to'],
            'value': txn['value']
        })

        maxUsedGas = Web3.fromWei(gas * Web3.toWei(txn['gasPrice'], 'gwei'), 'ether')
        value = txn['value'] - maxUsedGas

        logging.info('Max transaction cost: %s', str(maxUsedGas))
        return gas, int(value)


    def connect(self, provider):
        if provider[:2].lower() == 'ws':
            w3 = Web3(Web3.WebsocketProvider(provider))
        else:
            w3 = Web3(Web3.HTTPProvider(provider))
        return w3


if __name__ == '__main__':
    try:
        Hunter()
    except KeyboardInterrupt:
        exit()
