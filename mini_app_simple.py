from flask import Flask, render_template, request, jsonify, make_response
import uuid
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nft-gifts-mini-app-secret-key'

# Конфигурация бота для уведомлений
BOT_TOKEN = "8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M"
ADMIN_ID = 8566238705

# Временное хранилище сделок (в памяти)
deals_storage = {}

# Убираем все предупреждения и добавляем CORS
@app.after_request
def after_request(response):
    """Убираем предупреждения и добавляем нужные заголовки"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['ngrok-skip-browser-warning'] = 'true'
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

# Главная страница Mini App
@app.route('/')
def index():
    response = make_response(render_template('mini_app/index.html'))
    return response

# Создание сделки
@app.route('/create')
def create_deal():
    return render_template('mini_app/create.html')

# Просмотр сделки
@app.route('/deal/<deal_id>')
def view_deal(deal_id):
    return render_template('mini_app/deal.html', deal_id=deal_id)

# API для получения сделки
@app.route('/api/deal/<deal_id>')
def api_get_deal(deal_id):
    try:
        if deal_id in deals_storage:
            deal = deals_storage[deal_id]
            return jsonify({'success': True, 'deal': deal})
        else:
            return jsonify({'success': False, 'message': 'Сделка не найдена'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# Профиль
@app.route('/profile')
def profile():
    return render_template('mini_app/profile_simple.html')

# API для получения данных пользователя (просто возвращаем username)
@app.route('/api/user_profile')
def api_user_profile():
    try:
        username = request.args.get('username', 'Пользователь')
        first_name = request.args.get('first_name', '')
        
        return jsonify({
            'success': True, 
            'user': {
                'username': username,
                'first_name': first_name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для создания сделки
@app.route('/api/create_deal', methods=['POST'])
def api_create_deal():
    try:
        data = request.get_json()
        telegram_user = data.get('telegram_user')
        
        if not telegram_user:
            return jsonify({'success': False, 'message': 'Не удалось получить данные пользователя'})
        
        deal_id = str(uuid.uuid4())[:8].upper()
        
        # Сохраняем сделку в памяти
        deal_data = {
            'id': deal_id,
            'seller_id': telegram_user['id'],
            'seller_name': telegram_user.get('first_name', 'Пользователь'),
            'seller_username': telegram_user.get('username', ''),
            'nft_link': data.get('nft_link'),
            'nft_username': data.get('nft_username'),
            'amount': data.get('amount'),
            'currency': data.get('currency'),
            'description': data.get('description'),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        deals_storage[deal_id] = deal_data
        
        # Отправляем уведомление админу
        notify_admin_about_deal(deal_data)
        
        deal_url = f"https://t.me/noscamnftrbot?start=deal_{deal_id}"
        
        return jsonify({
            'success': True,
            'deal_id': deal_id,
            'deal_url': deal_url,
            'message': 'Сделка создана! Администратор получил уведомление.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

# API для подтверждения оплаты админом
@app.route('/api/admin/confirm_payment', methods=['POST'])
def api_admin_confirm_payment():
    try:
        data = request.get_json()
        deal_id = data.get('deal_id')
        admin_id = data.get('admin_id')
        
        if str(admin_id) != str(ADMIN_ID):
            return jsonify({'success': False, 'message': 'Нет прав администратора'})
        
        if deal_id not in deals_storage:
            return jsonify({'success': False, 'message': 'Сделка не найдена'})
        
        deal = deals_storage[deal_id]
        deal['status'] = 'paid'
        deal['paid_at'] = datetime.now().isoformat()
        
        # Уведомляем продавца
        notify_seller_payment_confirmed(deal)
        
        return jsonify({
            'success': True,
            'message': f'Оплата подтверждена для сделки {deal_id}',
            'deal': deal
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

def notify_admin_about_deal(deal):
    """Отправляет уведомление администратору о новой сделке"""
    try:
        currency_symbols = {
            'stars': '⭐',
            'rub': '₽',
            'uah': '₴',
            'usd': '$',
            'eur': '€'
        }
        
        symbol = currency_symbols.get(deal['currency'], '')
        
        text = f"🆕 <b>Новая сделка создана!</b>\n\n" \
               f"🆔 <b>ID:</b> #{deal['id']}\n" \
               f"👤 <b>Продавец:</b> {deal['seller_name']}"
        
        if deal['seller_username']:
            text += f" (@{deal['seller_username']})"
        
        text += f"\n💰 <b>Сумма:</b> {symbol}{deal['amount']}\n" \
                f"🎁 <b>NFT:</b> {deal['nft_link']}\n" \
                f"📝 <b>Описание:</b> {deal['description'] or 'Не указано'}\n\n" \
                f"⏳ <b>Статус:</b> Ожидает оплаты"
        
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Подтвердить оплату",
                        "callback_data": f"confirm_payment_{deal['id']}"
                    }
                ],
                [
                    {
                        "text": "❌ Отклонить сделку",
                        "callback_data": f"reject_deal_{deal['id']}"
                    }
                ]
            ]
        }
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_ID,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Уведомление о сделке {deal['id']} отправлено администратору")
        else:
            print(f"❌ Ошибка отправки уведомления: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка уведомления администратора: {e}")

def notify_seller_payment_confirmed(deal):
    """Уведомляет продавца о подтверждении оплаты"""
    try:
        currency_symbols = {
            'stars': '⭐',
            'rub': '₽',
            'uah': '₴',
            'usd': '$',
            'eur': '€'
        }
        
        symbol = currency_symbols.get(deal['currency'], '')
        
        text = f"✅ <b>Оплата подтверждена!</b>\n\n" \
               f"🆔 <b>Сделка:</b> #{deal['id']}\n" \
               f"💰 <b>Сумма:</b> {symbol}{deal['amount']}\n\n" \
               f"Теперь вы можете передать NFT покупателю.\n" \
               f"После передачи средства будут зачислены на ваш баланс.\n\n" \
               f"⚠️ <b>Важно:</b> Если сомневаетесь в покупателе, вы можете получить звёзды до передачи NFT.\n" \
               f"Звёзды хранятся на балансе бота. Для их получения напишите в поддержку."
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": deal['seller_id'],
            "text": text,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Уведомление продавцу отправлено")
        else:
            print(f"❌ Ошибка отправки уведомления продавцу: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка уведомления продавца: {e}")

if __name__ == '__main__':
    print("🚀 Запуск Mini App без базы данных...")
    print("📱 Открывайте: http://localhost:3000")
    app.run(host='0.0.0.0', port=3000, debug=True)
