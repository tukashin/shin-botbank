import os
from flask import Flask, request, jsonify
import ccxt

app = Flask(__name__)

# ==========================================
# bitbank API接続設定（信用取引モード）
# ==========================================
API_KEY = os.environ.get('BITBANK_API_KEY')
API_SECRET = os.environ.get('BITBANK_API_SECRET')

exchange = ccxt.bitbank({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    # 💥ここが超重要！信用取引（レバレッジ）を行うための設定です
    'options': {
        'defaultType': 'margin' 
    }
})

@app.route('/status', methods=['GET'])
def status():
    return "FRIDAY OVERDRIVE ACTIVE (MARGIN MODE)", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # 🔐 セキュリティチェック（合言葉の検証）
    if not data or data.get('password') != 'friday':
        return jsonify({"status": "error", "message": "Invalid password"}), 403
        
    action = data.get('action')
    symbol = 'BTC/JPY' # ビットコイン信用取引
    amount = 0.001     # 💥注文するBTCの枚数（最低注文数量付近にセットしています）

    try:
        if action == 'buy':
            # 📈 ロング（新規に買い注文を入れる）
            order = exchange.create_market_buy_order(symbol, amount)
            print(f"SUCCESS: Margin Long Order Executed! {order['id']}")
            return jsonify({"status": "success", "message": "Margin Long executed"}), 200
            
        elif action == 'sell':
            # 📉 ショート（新規に空売り注文を入れる）
            order = exchange.create_market_sell_order(symbol, amount)
            print(f"SUCCESS: Margin Short Order Executed! {order['id']}")
            return jsonify({"status": "success", "message": "Margin Short executed"}), 200
            
        else:
            return jsonify({"status": "error", "message": "Unknown action"}), 400
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
