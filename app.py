import time
from flask import Flask, request, jsonify
import ccxt

app = Flask(__name__)

# bitbank APIクライアント初期化（認証情報は環境変数から取得）
exchange = ccxt.bitbank({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
    'enableRateLimit': True
})

SYMBOL = 'BTC/JPY'
FIXED_AMOUNT = 0.001  # テスト運用サイズ

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        # 1. 認証プロトコル
        if not data or data.get("password") != "friday":
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        target_action = data.get("action")  # 'buy' または 'sell'
        if target_action not in ['buy', 'sell']:
            return jsonify({"status": "error", "message": "Invalid action"}), 400

        print(f"--- SIGNAL RECEIVED: {target_action.upper()} ---")

        # 2. 信用口座のアクティブポジションの現地現物確認
        # bitbank独自の信用アクティブポジション取得 API を直接コール
        position_res = exchange.privateGetMarginPositionActive()
        active_positions = position_res.get('data', {}).get('positions', [])
        
        # BTC/JPY のポジションのみを抽出
        btc_positions = [p for p in active_positions if p.get('pair') == 'btc_jpy']

        # 3. 既存ポジションの決済処理（双方向モードの相殺ロジック）
        for pos in btc_positions:
            pos_id = pos.get('position_id')
            pos_side = pos.get('side')  # 'buy' (long) または 'sell' (short)
            pos_amount = float(pos.get('amount', 0))

            # シグナルと逆のポジション、または既存ポジションが存在する場合は全決済
            print(f"Existing position found: ID={pos_id}, Side={pos_side}, Amount={pos_amount}")
            
            # 決済注文の方向を決定（ロング決済ならsell、ショート決済ならbuy）
            close_side = 'sell' if pos_side == 'buy' else 'buy'
            
            # position_id を明示的に指定して成行決済注文を執行
            close_order = exchange.create_order(
                symbol=SYMBOL,
                type='market',
                side=close_side,
                amount=pos_amount,
                params={'position_id': pos_id}
            )
            print(f"SUCCESS: Position Close Executed. Order ID: {close_order['id']}")
            
            # クリティカル・ウェイト：nonce（タイムスタンプ）の衝突を100%回避するインターバル
            time.sleep(1.5)

        # 4. 新規ドテンエントリー処理
        print(f"Executing New Target Entry: {target_action.upper()} | Amount: {FIXED_AMOUNT}")
        if target_action == 'buy':
            new_order = exchange.create_market_buy_order(SYMBOL, FIXED_AMOUNT)
        else:
            new_order = exchange.create_market_sell_order(SYMBOL, FIXED_AMOUNT)
            
        print(f"SUCCESS: New Entry Executed. Order ID: {new_order['id']}")
        return jsonify({"status": "success", "message": f"Friday system flipped to {target_action}"}), 200

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
