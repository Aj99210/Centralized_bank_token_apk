from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Database file
DB_FILE = 'bank_database.json'

# Initialize database
def init_db():
    if not os.path.exists(DB_FILE):
        data = {
            'users': {},
            'transactions': []
        }
        save_db(data)
    return load_db()

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize on startup
init_db()

@app.route('/join_bank', methods=['POST'])
def join_bank():
    data = request.json
    username = data.get('username')
    bank = data.get('bank')
    
    if not username or not bank:
        return jsonify({'success': False, 'message': 'Username and bank required'})
    
    db = load_db()
    
    if username in db['users']:
        return jsonify({'success': True, 'message': f'Welcome back, {username}!'})
    
    db['users'][username] = {
        'bank': bank,
        'balance': 0,
        'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_db(db)
    return jsonify({'success': True, 'message': f'Successfully joined {bank}!'})

@app.route('/mint_tokens', methods=['POST'])
def mint_tokens():
    data = request.json
    username = data.get('username')
    amount = data.get('amount')
    
    if not username or not amount:
        return jsonify({'success': False, 'message': 'Username and amount required'})
    
    db = load_db()
    
    if username not in db['users']:
        return jsonify({'success': False, 'message': 'User not found'})
    
    db['users'][username]['balance'] += amount
    
    # Record transaction
    db['transactions'].append({
        'from': 'SYSTEM',
        'to': username,
        'amount': amount,
        'type': 'mint',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    save_db(db)
    return jsonify({'success': True, 'message': f'Minted {amount} tokens', 'new_balance': db['users'][username]['balance']})

@app.route('/transfer_tokens', methods=['POST'])
def transfer_tokens():
    data = request.json
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    amount = data.get('amount')
    
    if not from_user or not to_user or not amount:
        return jsonify({'success': False, 'message': 'All fields required'})
    
    db = load_db()
    
    if from_user not in db['users']:
        return jsonify({'success': False, 'message': 'Sender not found'})
    
    if to_user not in db['users']:
        return jsonify({'success': False, 'message': 'Recipient not found'})
    
    if db['users'][from_user]['balance'] < amount:
        return jsonify({'success': False, 'message': 'Insufficient balance'})
    
    # Perform transfer
    db['users'][from_user]['balance'] -= amount
    db['users'][to_user]['balance'] += amount
    
    # Record transaction
    db['transactions'].append({
        'from': from_user,
        'to': to_user,
        'amount': amount,
        'type': 'transfer',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    save_db(db)
    return jsonify({'success': True, 'message': f'Transferred {amount} tokens to {to_user}'})

@app.route('/get_balance/<username>', methods=['GET'])
def get_balance(username):
    db = load_db()
    
    if username not in db['users']:
        return jsonify({'success': False, 'balance': 0})
    
    return jsonify({'success': True, 'balance': db['users'][username]['balance']})

@app.route('/get_bank_stats', methods=['GET'])
def get_bank_stats():
    db = load_db()
    
    bank_stats = {}
    for username, user_data in db['users'].items():
        bank = user_data['bank']
        bank_stats[bank] = bank_stats.get(bank, 0) + 1
    
    total_users = len(db['users'])
    total_tokens = sum(user['balance'] for user in db['users'].values())
    
    return jsonify({
        'success': True,
        'bank_stats': bank_stats,
        'total_users': total_users,
        'total_tokens': total_tokens
    })

@app.route('/get_transactions/<username>', methods=['GET'])
def get_transactions(username):
    db = load_db()
    
    user_transactions = [
        tx for tx in db['transactions']
        if tx['from'] == username or tx['to'] == username
    ]
    
    # Get last 10 transactions
    user_transactions = sorted(user_transactions, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    return jsonify({'success': True, 'transactions': user_transactions})

@app.route('/get_all_users', methods=['GET'])
def get_all_users():
    db = load_db()
    
    users_list = []
    for username, user_data in db['users'].items():
        users_list.append({
            'username': username,
            'bank': user_data['bank'],
            'balance': user_data['balance'],
            'joined_at': user_data['joined_at']
        })
    
    return jsonify({'success': True, 'users': users_list})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    print("🏦 Bank Token System Server Starting...")
    print("📡 Server running on http://localhost:5000")
    print("💾 Database file: bank_database.json")

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

