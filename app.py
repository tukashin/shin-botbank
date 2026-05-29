import os
import ccxt
from flask import Flask, request, jsonify

app = Flask(__name__)

# bitbank認証設定
bitbank = ccxt.bitbank({
    'apiKey': os.getenv('BITBANK_API_KEY'),
    'secret': os.getenv('BITBANK_API_SECRET'),
})

@app.route('/status', methods=['GET'])
def status():
    return "FRIDAY OVERDRIVE ACTIVE", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data or data.get('password') != 'friday':
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        action = data.get('action')
        amount_jpy = 3000  # 1回の予算
        
        if action == 'buy':
            ticker = bitbank.fetch_ticker('BTC/JPY')
            btc_price = ticker['last']
            amount_btc = round(amount_jpy / btc_price, 4)
            
            order = bitbank.create_market_buy_order('BTC/JPY', amount_btc)
            return jsonify({"status": "success", "order": order}), 200
            
        return jsonify({"status": "ignored", "message": "No action taken"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
