#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, make_response
import uuid, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nft-uz-secret'

BOT_TOKEN = "8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M"
ADMIN_ID  = 8566238705
deals_storage = {}

@app.after_request
def after_request(r):
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    r.headers['X-Frame-Options']              = 'ALLOWALL'
    r.headers['Content-Security-Policy']      = 'frame-ancestors *'
    return r

@app.route('/')
def index():
    return render_template('mini_app/index.html')

@app.route('/create')
def create_deal():
    return render_template('mini_app/create.html')

@app.route('/deals')
def deals():
    return render_template('mini_app/deals.html')

@app.route('/deal/<deal_id>')
def deal(deal_id):
    return render_template('mini_app/deal.html', deal_id=deal_id)

@app.route('/profile')
def profile():
    return render_template('mini_app/profile_simple.html')

@app.route('/admin')
def admin():
    return render_template('mini_app/admin.html')

# ── Foydalanuvchi profili (ma'lumotlar bazasidan) ──
@app.route('/api/user_profile')
def api_user_profile():
    try:
        telegram_id = request.args.get('telegram_id','')
        username    = request.args.get('username','')
        first_name  = request.args.get('first_name','')
        user_data   = {
            'username': username, 'first_name': first_name,
            'balance_stars': 0, 'ton_wallet': None,
            'successful_deals': 0, 'verified': False, 'uid': None,
        }
        if telegram_id:
            try:
                conn = sqlite3.connect('data/unified.db')
                c    = conn.cursor()
                c.execute(
                    'SELECT balance_stars,ton_wallet,successful_deals,verified,uid FROM users WHERE telegram_id=?',
                    (str(telegram_id),)
                )
                row = c.fetchone(); conn.close()
                if row:
                    user_data['balance_stars']    = row[0] or 0
                    user_data['ton_wallet']        = row[1]
                    user_data['successful_deals']  = row[2] or 0
                    user_data['verified']          = bool(row[3])
                    user_data['uid']               = row[4]
            except Exception as e:
                print(f"DB xato: {e}")
        return jsonify({'success': True, 'user': user_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ── Bitim yaratish ──
@app.route('/api/create_deal', methods=['POST'])
def api_create_deal():
    try:
        data = request.get_json()
        tg_user = data.get('telegram_user')
        if not tg_user:
            return jsonify({'success': False, 'message': "Telegram ma'lumotlari topilmadi"})

        deal_id = str(uuid.uuid4())[:8].upper()
        deal_data = {
            'id': deal_id,
            'seller_id':       tg_user['id'],
            'seller_name':     tg_user.get('first_name','Foydalanuvchi'),
            'seller_username': tg_user.get('username',''),
            'nft_link':        data.get('nft_link'),
            'nft_username':    data.get('nft_username'),
            'amount':          data.get('amount'),
            'currency':        'stars',
            'description':     data.get('description'),
            'status':          'active',
            'created_at':      datetime.now().isoformat()
        }
        deals_storage[deal_id] = deal_data

        import requests as req
        req.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', json={
            'chat_id': ADMIN_ID,
            'text': (
                f"📦 Yangi bitim yaratildi\n\n"
                f"ID: {deal_id}\n"
                f"Sotuvchi: {deal_data['seller_name']}\n"
                f"Narxi: {deal_data['amount']} Stars\n"
                f"NFT: {deal_data.get('nft_username','')}"
            ),
            'parse_mode': 'HTML'
        })

        return jsonify({
            'success':  True,
            'deal_id':  deal_id,
            'deal_url': f"https://t.me/noscamnftrbot?start=deal_{deal_id}",
            'message':  "Bitim yaratildi!"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ── Bitimlar ro'yxati ──
@app.route('/api/deals')
def api_deals():
    active = [d for d in deals_storage.values() if d.get('status') == 'active']
    return jsonify({'success': True, 'deals': active})

@app.route('/api/deal/<deal_id>')
def api_deal(deal_id):
    deal = deals_storage.get(deal_id)
    if deal:
        return jsonify({'success': True, 'deal': deal})
    return jsonify({'success': False, 'message': "Bitim topilmadi"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
