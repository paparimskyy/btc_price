from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)


valuti = ['usd', 'eur', 'rub', 'gbp', 'jpy', 'cny']

def get_bitcoin_price_coingecko():
    """
    Получение курса биткоина через CoinGecko API
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin',
            'vs_currencies': ','.join(valuti),
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('bitcoin', {})
    
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к CoinGecko API: {e}")
        return None

def get_bitcoin_history():
    """
    Получение исторических данных для графика (последние 30 дней)
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '30',
            'interval': 'daily'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
      
        prices = []
        for i, price_data in enumerate(data['prices']):
           
            if i % 3 == 0:
                timestamp = price_data[0]
                price = price_data[1]
                date = datetime.fromtimestamp(timestamp/1000).strftime('%d.%m')
                prices.append({
                    'date': date,
                    'price': round(price, 2)
                })
        
        return prices[-10:]  
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении исторических данных: {e}")
        
        return generate_sample_data()

def generate_sample_data():
    """
    Генерирует примерные данные если API не доступно
    """
    sample_data = []
    base_price = 45000
    for i in range(10):
        date = (datetime.now() - timedelta(days=10-i)).strftime('%d.%m')
       
        price_variation = (i * 300) - (i % 2 * 800) + (i % 3 * 400)
        price = base_price + price_variation
        sample_data.append({
            'date': date,
            'price': price
        })
    return sample_data

@app.route('/')
def index():
    """
    Главная страница с отображением курса биткоина и графика
    """
    bitcoin_data = get_bitcoin_price_coingecko()
    history_data = get_bitcoin_history()
    
    if bitcoin_data and history_data:
       
        formatted_data = {}
        for currency in valuti:
            if currency in bitcoin_data:
                price = bitcoin_data.get(currency, 0)
                change_24h = bitcoin_data.get(f'{currency}_24h_change', 0)
                
                
                if currency == 'rub':
                    formatted_price = f"{price:,.0f}".replace(',', ' ')
                elif price > 1:
                    formatted_price = f"{price:,.2f}"
                else:
                    formatted_price = f"{price:.6f}"
                
                formatted_data[currency.upper()] = {
                    'price': formatted_price,
                    'change_24h': f"{change_24h:.2f}%",
                    'change_class': 'positive' if change_24h > 0 else 'negative'
                }
        
       
        chart_labels = [point['date'] for point in history_data]
        chart_prices = [point['price'] for point in history_data]
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('index.html', 
                             bitcoin_data=formatted_data,
                             chart_labels=chart_labels,
                             chart_prices=chart_prices,
                             last_updated=last_updated)
    else:
        return render_template('error.html', 
                             message="Не удалось получить данные о курсе биткоина")

@app.route('/api/price')
def api_price():
    """
    JSON API endpoint для получения текущего курса
    """
    bitcoin_data = get_bitcoin_price_coingecko()
    
    if bitcoin_data:
        return jsonify({
            'success': True,
            'data': bitcoin_data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch Bitcoin price'
        }), 500

@app.route('/api/history')
def api_history():
    """
    JSON API endpoint для получения исторических данных
    """
    history_data = get_bitcoin_history()
    
    if history_data:
        return jsonify({
            'success': True,
            'data': history_data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch historical data'
        }), 500

@app.route('/health')
def health_check():
    """
    Endpoint для проверки работоспособности приложения
    """
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message="Страница не найдена"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="Внутренняя ошибка сервера"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)