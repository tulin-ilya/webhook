import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import *
from binance.enums import *
# import math

# ----Фьючерсы
    # - Разместить STOP ордер   | client.futures_create_order(price='2650.0', stopPrice='2650.0', side='BUY', quantity='0.005', symbol='ETHUSDT', type='STOP')
    # - Разместить MARKET ордер | client.futures_create_order(side='BUY', quantity='0.005', symbol='ETHUSDT', type='MARKET')
    # - Удалить STOP ордер      | client.futures_cancel_order( symbol='ETHUSDT',orderId ='8389765495335554298' )


app = Flask(__name__)
client = Client(config.APIkey, config.APIsecret)

#Для спота нужно тестировать
    # class getExInfoSymb_spot():
    #     allsymb = {}
    #     def __init__(self, client):
    #         self.client = client
    #     def getSymbInfoFromExchange(self,symb):
    #         try:
    #             self.allsymb[symb]
    #         except:
    #             self.allsymb[symb] = self.client.get_symbol_info(symb)
    #     def getSymbPrecisionInfo(self, symb):
    #         self.getSymbInfoFromExchange(symb)

    #         if self.allsymb[symb] == None:
    #             print(str(symb) + ' symb, class getExInfoSymb- error "This Symb is not exsist!"')
    #             return None

    #         step_size = 0.0
    #         for f in self.allsymb[symb]['filters']:
    #             if f['filterType'] == 'LOT_SIZE':
    #                 step_size = float(f['stepSize'])

    #         precision = int(round(-math.log(step_size, 10), 0))
    #         return precision


# /------- Получаем precision (кол-во цифр после запятой) для ордера -------/#

class getExInfoSymb():
    allsymb = None

    def __init__(self, client):
        self.client     = client
        self.allsymb    = self.client.futures_exchange_info()['symbols']

    def getSymbInfo(self, symb):
        for this_symb in self.allsymb:
            if this_symb['symbol'] == symb:
                return this_symb

getExInfoSymb = getExInfoSymb(client=client)

# /------- Формируем функцию ордера -------/#

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        order = client.futures_create_order(
            symbol      = symbol, 
            side        = side, 
            quantity    = quantity, 
            type        = order_type)

    except Exception as e:
        print("!!!an exception occured!!! - {}".format(e))
        return False

    return order

# /------- Страница заглушка -------/#

@app.route('/')
def index():
    return render_template('index.html')

# /------- Вебхук -------/#

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Invalid passphrase"
        }

    print(data['ticker'])
    print(data['time'])

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']

    # /------- Меняем имя тикера (с PERP на USDT) -------/#

    ticker      = data['ticker']                                # получаем из аллерта тикер вида "coin_namePERP"
    splitTicker = ticker.split('PERP')                          # разделяем тикер на "coin_name" и "PERP"
    coin        = splitTicker[0]                                # забираем из splitTicker "coin_name"


    if len( splitTicker ) == 2:                                 # проверка что правильно строка разделена на coin_name и PERP
        ticker = coin + 'USDT'                                  # соединяем coin_name и quote
    else:
        return {
            'code': 'error',                                    # если строка заделена не верно, сообщение об ошибке
            'message': 'no symbol match'
        }

    order_response = order(side, round(float(quantity), getExInfoSymb.getSymbInfo(ticker)['quantityPrecision']), ticker)

    if order_response:
        print("order success")
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")
        return {
            "code": "error",
            "message": "order failed"
        }