import json
import requests
import sys
import threading
import time
from datetime import datetime
import math
from library.prediction import Token
import os
import logging.config

if not os.path.exists('logs'):
    os.mkdir('logs')
today = datetime.today()
logging.config.dictConfig({
    "version":                  1,
    "disable_existing_loggers": False,
    "formatters":               {
        "default": {
            "format": "%(asctime)s %(message)s"
        }
    },
    "handlers":                 {
        "console": {
            "class":     "logging.StreamHandler",
            "level":     "INFO",
            "formatter": "default",
            "stream":    "ext://sys.stdout"
        },
        "file":    {
            "class":     "logging.FileHandler",
            "level":     "INFO",
            "formatter": "default",
            "filename":  f"logs/debug-{today.year}-{today.month}-{today.day}-{today.hour}.log",
            "mode":      "a",
            "encoding":  "utf-8"
        }
    },
    "root":                     {
        "level":    "INFO",
        "handlers": [
            "console",
            "file"
        ]
    }
})
LOGGER = logging.getLogger()

class PredictionBot():
    def __init__(self):
        self.wallet = None
        self.w3 = None
        self.w3_wss = None
        self.wallet_connected = False
        self.wallet_address = ""
        self.private_key = ""
        self.prediction_address = "0x516ffd7D1e0Ca40b1879935B2De87cb20Fc1124b"
        self.usdt = "0x55d398326f99059ff775485246999027b3197955"
        self.provider = ""
        self.provider_wss = False
        self.current_price = 0
        self.current_id = 1
        self.current_bet_id = False
        self.current_round = None
        self.current_up_rate = 1
        self.current_down_rate = 1
        self.current_prize = 0
        self.up_amount = 0
        self.down_amount = 0
        self.remain_time = 300
        self.claim_id = 6591
        self.balance = 0
        self.bot_flag = False
        self.bet_amount = 1
        self.limit = 0
        self.time_limit = 8
        self.up = 0
        self.down = 0
        self.interval = 30
        self.bear = 0
        self.bull = 0
        self.event_time = 10
        self.old_price = 0
        self.period_time = 0
        self.betted_id = []
        self.lock_price = 0
        self.gas_limit = 500000
        self.target_address = ''
        self.id_list = list()
        self.default_bet_amount = 0.02
        self.low_bet_amount = 0.05
        self.medium_bet_amount = 0.1
        self.high_bet_amount = 0.2
        self.previous_chain_price = 0
        self.betting_platform = 1# 1: pancakeswap, 2: Dogebet
        self.wallet_connect()

    def read_config(self):
        try:
            with open('config.json') as f:
                data = json.load(f)
                self.provider = data['provider_bsc']
                self.wallet_address = data['address']
                self.private_key = data['private_key']
                self.target_address = data['address']
                self.target_address = self.target_address.lower()
                self.event_time = int(data['event_time'])
                self.gas_limit = int(data['gas_limit'])
                self.default_bet_amount = float(data['default_bet_amount'])
                self.low_bet_amount = float(data['low_bet_amount'])
                self.medium_bet_amount = float(data['medium_bet_amount'])
                self.high_bet_amount = float(data['high_bet_amount'])
                self.down_amount = int(self.default_bet_amount*10**18)
                self.up_amount = int(self.default_bet_amount*10**18)
                self.bet_amount = 1
                print('Read Config Success')
        except Exception as e:
            print(e)
            print("Config file read failed...")

    def wallet_connect(self):
        self.wallet_connected = False
        self.read_config()
        try:
            self.wallet = Token(
                address=self.usdt,
                provider=self.provider
            )
            self.wallet.connect_wallet(self.wallet_address, self.private_key)
            if self.wallet.is_connected():
                self.wallet_connected = True
                self.balance = self.wallet.web3.eth.getBalance(
                    self.wallet.web3.toChecksumAddress(self.wallet_address.lower()))
                print(
                    f'Balance : {round(self.balance / (10 ** 18), 3)}, Target : {self.target_address}, Gas_limit : {self.gas_limit}, Time_limit : {self.event_time}')
                print("Wallet Connect!")
                print("Please Select Betting Platform- [1]: Pancakeswap, [2]: Dogebet")
                self.betting_platform = int(input(":"))
                self.wallet.betting_platform = self.betting_platform
                self.wallet.set_gas_limit(gas_price=5, gas_limit=self.gas_limit)
                self.start_prediction()

        except Exception as e:
            self.wallet_connected = False
            print('Wallet Not Connected')
            print(e)

    def start_prediction(self):
        self.get_round()
        while True:
            self.remain_time = self.get_remain_time()
            if self.remain_time == 7:
                threading.Thread(target=self.main_bet_func).start()
            self.remain_time -= 1
            if self.remain_time <= 0:
                self.get_round()
            if self.remain_time == 260:
                threading.Thread(target=self.claim).start()
            time.sleep(1)
    def main_bet_func(self):
        chain_price = float(self.wallet.price()/(10**8))
        binance_price = self.wallet.current_price() + 0.3
        print("binance_price==>", binance_price, "chain_price==>", chain_price)
        bet_delta = abs(chain_price - binance_price)
        if self.previous_chain_price != 0 and abs(self.previous_chain_price - binance_price) > 1.5:
            amounts=int(self.high_bet_amount*(10**18))
            self.wallet.tx_bet(id=self.current_id, amount=amounts)
            self.bet_amount = self.high_bet_amount
            if self.previous_chain_price >= binance_price:
                threading.Thread(target=self.send_bet_bull).start()
            else:
                threading.Thread(target=self.send_bet_bear).start()
            self.previous_chain_price = chain_price
            return
        self.previous_chain_price = chain_price
        if bet_delta < 0.35:
            return
        if 0.5 <= bet_delta < 1.0 :
            amounts=int(self.low_bet_amount*(10**18))
            self.wallet.tx_bet(id=self.current_id, amount=amounts)
            self.bet_amount = self.low_bet_amount
            if binance_price >= chain_price:
                threading.Thread(target=self.send_bet_bull).start()
            else:
                threading.Thread(target=self.send_bet_bear).start()
            return
        if 1.0 <= bet_delta < 1.5 :
            amounts=int(self.medium_bet_amount*(10**18))
            self.wallet.tx_bet(id=self.current_id, amount=amounts)
            self.bet_amount = self.medium_bet_amount
            if binance_price >= chain_price:
                threading.Thread(target=self.send_bet_bull).start()
            else:
                threading.Thread(target=self.send_bet_bear).start()
            return
        if 1.5 <= bet_delta :
            amounts=int(self.high_bet_amount*(10**18))
            self.wallet.tx_bet(id=self.current_id, amount=amounts)
            self.bet_amount = self.high_bet_amount
            if binance_price >= chain_price:
                threading.Thread(target=self.send_bet_bull).start()
            else:
                threading.Thread(target=self.send_bet_bear).start()
            return
        if self.current_id % 2 == 0:
            self.wallet.tx_bet(id=self.current_id, amount=self.down_amount)
            self.bet_amount = self.down_amount
        else:
            self.wallet.tx_bet(id=self.current_id, amount=self.up_amount)
            self.bet_amount = self.up_amount
        if binance_price >= chain_price:
            threading.Thread(target=self.send_bet_bear).start()
        else:
            threading.Thread(target=self.send_bet_bull).start()


    def get_remain_time(self):
        if self.betting_platform == 1:
            d_time = int(self.current_round[2] - datetime.now().timestamp())
        else:
            d_time = int(self.current_round[8] - datetime.now().timestamp())
        remain_time = d_time
        return remain_time

    def get_round(self):
        self.current_id = self.wallet.get_current_Epoch()
        self.current_round = self.wallet.get_round(id=self.current_id)

    def mempool(self):
        event_filter = self.wallet.web3.eth.filter("pending")
        while self.bot_flag:
            try:
                new_entries = event_filter.get_new_entries()
                threading.Thread(target=self.get_events, args=(new_entries, )).start()
            except Exception as err:
                # print(err)
                print("error")
                pass

    def get_events(self, new_entries):
        try:
            for event in new_entries[::-1]:
                try:
                    threading.Thread(target=self.handle_event, args=(event,)).start()
                    if self.bot_flag == False:
                        break
                except Exception as e:
                    print(e)
                    pass
        except:
            pass

    def handle_event(self, event):
        try:
            transaction = self.wallet.web3.eth.getTransaction(event)
            if transaction['from'].lower() == self.target_address and transaction.input[:10].lower() == '0xaa6b873a':
                threading.Thread(target=self.send_bet_bear).start()
                self.bot_flag = False
            elif transaction['from'].lower() == self.target_address and transaction.input[:10].lower() == '0x57fb096f':
                threading.Thread(target=self.send_bet_bull).start()
                self.bot_flag = False
        except Exception as e:
            pass

    

    def send_bet_bull(self):
        result = self.wallet.send_bet_bull()
        self.betted_id.append(self.current_id)
        LOGGER.info(f'{self.current_id}-Bull ===> {self.bet_amount} : {result.hex()}')
        if self.current_id % 2 == 0:
            self.provider_wss = True
        else:
            self.current_bet_id = True

    def send_bet_bear(self):
        result = self.wallet.send_bet_bear()
        self.betted_id.append(self.current_id)
        LOGGER.info(f'{self.current_id}-Bear ===> {self.bet_amount} : {result.hex()}')
        if self.current_id % 2 == 0:
            self.provider_wss = True
        else:
            self.current_bet_id = True

    def claim(self):
        claim_id = self.current_id-2
        claim_flag = self.wallet.claimAble(claim_id)
        if claim_flag:
            result = self.wallet.claim(id=int(claim_id))
            if self.current_id % 2 == 0 and self.provider_wss == True:
                self.provider_wss = False
                self.down_amount=int(self.default_bet_amount*(10**18))
            if self.current_id % 2 == 1 and self.current_bet_id == True:
                self.current_bet_id = False
                self.up_amount=int(self.default_bet_amount*(10**18))
            LOGGER.info(f'Claim ID - {claim_id}, You Win! {result.hex()}')
        else:
            if self.current_id % 2 == 0 and self.provider_wss == True:
                self.provider_wss = False
                amount = self.down_amount
                self.down_amount = int(amount * 2)
                if self.down_amount > int(self.medium_bet_amount*(10**18)):
                    self.down_amount = int(self.medium_bet_amount*(10**18))
            if self.current_id % 2 == 1 and self.current_bet_id == True:
                self.current_bet_id = False
                amount = self.up_amount
                self.up_amount = int(amount * 2)
                if self.up_amount > int(self.medium_bet_amount*(10**18)):
                    self.up_amount = int(self.medium_bet_amount*(10**18))
            if claim_id in self.betted_id:
                LOGGER.info(f'Claim ID - {claim_id}, You Lost!')
            else:
                LOGGER.info(f'Claim ID - {claim_id}, No Bet!')
if __name__ == '__main__':
    bot = PredictionBot()
    bot.wallet_connect()
