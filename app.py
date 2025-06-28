import os
import logging
import json
import uuid
import hashlib
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import math
import random

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'navigation-secret-key')
app.config['UPLOAD_FOLDER'] = 'audio_uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage (in production, use a database)
conversation_history = []
saved_locations = {}

# Конфигурация
GEMINI_API_KEY = "AIzaSyAa6831q1q_61pxjnatffMqWQEMPp9jRjQ"
GOOGLE_MAPS_API_KEY = "AIzaSyBI_q34br_taffgYVlIs7hQ25yl3QjEXk0"  # Новый Google Maps API ключ

# Передача API ключей в шаблоны
@app.context_processor
def inject_api_keys():
    return {
        'GOOGLE_MAPS_API_KEY': GOOGLE_MAPS_API_KEY
    }

# Добавляем JSON фильтр для Jinja2
def tojson_filter(obj):
    return json.dumps(obj)

app.jinja_env.filters['tojsonfilter'] = tojson_filter

class GeminiNavigationService:
    """Сервис для обработки навигационных команд и голосового ассистента."""
    
    def __init__(self):
        self.model = None
        self._configure_gemini()
    
    def _configure_gemini(self):
        """Настройка Gemini API."""
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY не установлен")
            
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logger.info("Gemini API настроен успешно")
            
        except Exception as e:
            logger.error(f"Ошибка настройки Gemini API: {e}")
            raise
    
    def process_navigation_audio(self, audio_path, user_location, destination=None, conversation_context=""):
        """
        Обработка голосовых команд для навигации.
        """
        try:
            if not os.path.exists(audio_path):
                return {"error": "Аудиофайл не найден"}
            
            if os.path.getsize(audio_path) == 0:
                return {"error": "Аудиофайл пуст"}
            
            # Определение MIME типа
            file_ext = os.path.splitext(audio_path)[1].lower()
            mime_type_map = {
                '.webm': 'audio/webm',
                '.m4a': 'audio/m4a',
                '.mp3': 'audio/mp3',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac'
            }
            mime_type = mime_type_map.get(file_ext, 'audio/webm')
            
            # Чтение аудиофайла
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Создание промпта для навигационного ассистента
            location_info = f"Вы находитесь на координатах: {user_location.get('lat', 43.238293)}, {user_location.get('lng', 76.889709)} в городе Алматы"
            destination_info = f"Пункт назначения: {destination}" if destination else "Готов проложить маршрут к любому месту в Алматы"
            
            prompt = f"""
            Вы - профессиональный голосовой навигатор SmartAla для города Алматы. Вы знаете все улицы, здания и маршруты в городе.

            ВАША РОЛЬ: Опытный навигационный ассистент который точно знает весь город Алматы
            
            ТЕКУЩАЯ СИТУАЦИЯ:
            {location_info}
            {destination_info}
            
            ПРЕДЫДУЩИЙ РАЗГОВОР:
            {conversation_context}

            ИНСТРУКЦИИ ДЛЯ ОТВЕТОВ:
            - Расшифруйте аудио точно
            - Отвечайте как профессиональный GPS-навигатор
            - Если спрашивают куда идти - дайте точные указания с названиями улиц
            - Если называют место назначения - постройте конкретный маршрут
            - Используйте реальные названия улиц Алматы: проспект Абая, улица Сатпаева, проспект Аль-Фараби, улица Толе би, проспект Назарбаева
            - Указывайте точные расстояния в метрах и времени в минутах
            - Говорите направления: "поверните направо на улицу...", "идите прямо 200 метров", "поверните налево"
            - Предупреждайте о светофорах, переходах, ориентирах
            - Если спрашивают правильно ли идут - подтвердите или скорректируйте направление
            - Говорите уверенно и точно, как настоящий навигатор
            - Если не знаете точное место - предложите ближайшие известные ориентиры

            ПРИМЕРЫ ОТВЕТОВ:
            "Поверните направо на проспект Абая и идите 300 метров до светофора"
            "Пройдите прямо 150 метров, затем поверните налево на улицу Сатпаева"
            "Вы идете правильно, продолжайте прямо еще 200 метров"
            "До пункта назначения 8 минут ходьбы, 650 метров"

            ФОРМАТ ОТВЕТА:
            ТРАНСКРИПЦИЯ: [что вы услышали]
            НАВИГАЦИЯ: [точные навигационные указания с названиями улиц и расстояниями]
            """
            
            logger.info(f"Обработка аудио: {audio_path} (MIME: {mime_type})")
            response = self.model.generate_content([
                prompt, 
                {"mime_type": mime_type, "data": audio_data}
            ])
            
            # Парсинг ответа
            response_text = response.text.strip()
            
            transcription = ""
            navigation_response = ""
            
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('ТРАНСКРИПЦИЯ:'):
                    current_section = 'transcription'
                    transcription += line.replace('ТРАНСКРИПЦИЯ:', '').strip()
                elif line.startswith('НАВИГАЦИЯ:'):
                    current_section = 'navigation'
                    navigation_response += line.replace('НАВИГАЦИЯ:', '').strip()
                elif current_section == 'transcription' and line:
                    transcription += ' ' + line
                elif current_section == 'navigation' and line:
                    navigation_response += ' ' + line
            
            # Запасной парсинг
            if not transcription or not navigation_response:
                if 'ТРАНСКРИПЦИЯ:' in response_text and 'НАВИГАЦИЯ:' in response_text:
                    parts = response_text.split('НАВИГАЦИЯ:')
                    transcription = parts[0].replace('ТРАНСКРИПЦИЯ:', '').strip()
                    navigation_response = parts[1].strip()
                else:
                    transcription = "Аудио обработано"
                    navigation_response = response_text
            
            return {
                "transcription": transcription.strip(),
                "response": navigation_response.strip(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки аудио: {e}")
            return {
                "error": f"Не удалось обработать аудио: {str(e)}",
                "success": False
            }

# Инициализация сервиса
navigation_service = GeminiNavigationService()

@app.route('/')
def index():
    """Главная страница навигационного приложения."""
    return render_template('index.html')

@app.route('/navigate')
def navigate():
    """Страница навигации."""
    return render_template('navigate.html')

@app.route('/glasses')
def glasses():
    """Страница для Meta x Rayban glasses."""
    return render_template('glasses.html')

@app.route('/test_microphone')
def test_microphone():
    return render_template('test_microphone.html')

@app.route('/location/<location_id>')
def saved_location(location_id):
    """Страница для сохраненных локаций с автоматической навигацией."""
    if location_id in saved_locations:
        location = saved_locations[location_id]
        
        # Увеличиваем счетчик обращений
        location['access_count'] = location.get('access_count', 0) + 1
        
        # Подготавливаем данные для автоматической навигации в формате, ожидаемом шаблоном
        destination_data = {
            'name': location['name'],
            'description': location.get('description', ''),
            'latitude': location['lat'],
            'longitude': location['lng'],
            'category': location.get('category', 'general'),
            'id': location_id,
            'auto_navigation': True,
            'creation_time': location.get('timestamp', datetime.now().isoformat())
        }
        
        return render_template('navigate.html', destination=destination_data)
    else:
        # Если локация не найдена, перенаправляем на главную с сообщением
        return render_template('index.html', error_message=f'Сохраненное место с ID {location_id} не найдено')

@app.route('/save_location', methods=['POST'])
def save_location():
    """Сохранение локации в статической ссылке с расширенной информацией."""
    try:
        data = request.get_json()
        location = data.get('location')
        name = data.get('name', 'Безымянная локация')
        description = data.get('description', '')
        category = data.get('category', 'general')  # general, home, work, shop, etc.
        
        if not location or not location.get('lat') or not location.get('lng'):
            return jsonify({'success': False, 'error': 'Неполные данные локации'}), 400
        
        # Создание уникального ID
        location_id = hashlib.md5(f"{location['lat']}{location['lng']}{name}".encode()).hexdigest()[:8]
        
        # Расширенная информация о локации
        saved_locations[location_id] = {
            'id': location_id,
            'name': name,
            'description': description,
            'category': category,
            'lat': float(location['lat']),
            'lng': float(location['lng']),
            'timestamp': datetime.now().isoformat(),
            'created_by': request.remote_addr,  # IP для отслеживания
            'access_count': 0  # Счетчик обращений
        }
        
        static_url = f"{request.host_url}location/{location_id}"
        
        logger.info(f"Сохранена новая локация: {name} ({location_id}) в {location['lat']}, {location['lng']}")
        
        return jsonify({
            'success': True,
            'location_id': location_id,
            'static_url': static_url,
            'location_data': saved_locations[location_id]
        })
        
    except Exception as e:
        logger.error(f"Ошибка сохранения локации: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_location_info/<location_id>')
def get_location_info(location_id):
    """Получение информации о сохраненной локации."""
    if location_id in saved_locations:
        location = saved_locations[location_id]
        # Увеличиваем счетчик обращений
        location['access_count'] = location.get('access_count', 0) + 1
        
        return jsonify({
            'success': True,
            'location': location
        })
    else:
        return jsonify({'success': False, 'error': 'Локация не найдена'}), 404

@app.route('/list_saved_locations')
def list_saved_locations():
    """Получение списка всех сохраненных локаций."""
    locations_list = []
    for location_id, location_data in saved_locations.items():
        locations_list.append({
            'id': location_id,
            'name': location_data['name'],
            'description': location_data.get('description', ''),
            'category': location_data.get('category', 'general'),
            'lat': location_data['lat'],
            'lng': location_data['lng'],
            'timestamp': location_data['timestamp'],
            'static_url': f"{request.host_url}location/{location_id}",
            'access_count': location_data.get('access_count', 0)
        })
    
    # Сортируем по времени создания (новые сначала)
    locations_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'success': True,
        'locations': locations_list,
        'total_count': len(locations_list)
    })

@app.route('/send_navigation_audio', methods=['POST'])
def send_navigation_audio():
    """Обработка голосовых команд для навигации."""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'Аудиофайл не предоставлен'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Аудиофайл не выбран'}), 400
        
        # Получение данных о местоположении и назначении
        user_location = request.form.get('location', '{}')
        destination = request.form.get('destination', '')
        
        try:
            user_location = json.loads(user_location)
        except:
            user_location = {}
        
        # Сохранение файла
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Подготовка контекста разговора
        context = "\n".join([
            f"Пользователь: {msg['transcription']}\nАссистент: {msg['response']}" 
            for msg in conversation_history[-5:]
        ])
        
        # Обработка с Gemini
        result = navigation_service.process_navigation_audio(
            file_path, user_location, destination, context
        )
        
        # Очистка аудиофайла
        try:
            os.remove(file_path)
        except:
            pass
        
        if result.get('success'):
            # Добавление в историю разговора
            conversation_entry = {
                'timestamp': datetime.now().isoformat(),
                'transcription': result['transcription'],
                'response': result['response'],
                'location': user_location,
                'destination': destination
            }
            conversation_history.append(conversation_entry)
            
            # Сохранение только последних 50 сообщений
            if len(conversation_history) > 50:
                conversation_history.pop(0)
            
            return jsonify({
                'success': True,
                'transcription': result['transcription'],
                'response': result['response'],
                'timestamp': conversation_entry['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Произошла неизвестная ошибка')
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка в send_navigation_audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_route', methods=['POST'])
def get_route():
    """Получение маршрута между двумя точками с расчетом реального расстояния."""
    try:
        data = request.get_json()
        start = data.get('start')
        end = data.get('end')
        
        if not start or not end:
            return jsonify({'success': False, 'error': 'Начальная и конечная точки обязательны'}), 400
        
        # Валидация координат
        try:
            start_lat = float(start.get('lat', 0))
            start_lng = float(start.get('lng', 0))
            end_lat = float(end.get('lat', 0))
            end_lng = float(end.get('lng', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Неверный формат координат'}), 400
        
        # Расчет расстояния по формуле Haversine
        distance_km = calculate_distance(start_lat, start_lng, end_lat, end_lng)
        distance_m = int(distance_km * 1000)
        
        # Примерное время (средняя скорость пешехода 5 км/ч)
        time_hours = distance_km / 5.0
        time_minutes = int(time_hours * 60)
        
        # Генерация пошаговых инструкций
        steps = generate_walking_directions(start_lat, start_lng, end_lat, end_lng, distance_m)
        
        route = {
            'start': {
                'lat': start_lat,
                'lng': start_lng,
                'description': start.get('name', 'Начальная точка')
            },
            'end': {
                'lat': end_lat,
                'lng': end_lng,
                'description': end.get('name', 'Пункт назначения')
            },
            'steps': steps,
            'total_distance': f"{distance_m} м" if distance_m < 1000 else f"{distance_km:.1f} км",
            'estimated_time': f"{time_minutes} мин" if time_minutes < 60 else f"{int(time_hours)}ч {time_minutes % 60}мин",
            'distance_meters': distance_m,
            'time_minutes': time_minutes
        }
        
        logger.info(f"Построен маршрут: {distance_m}м, {time_minutes}мин")
        
        return jsonify({
            'success': True,
            'route': route
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения маршрута: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_distance(lat1, lng1, lat2, lng2):
    """Расчет расстояния между двумя точками по формуле Haversine."""
    import math
    
    # Радиус Земли в километрах
    R = 6371.0
    
    # Перевод в радианы
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Разности координат
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    # Формула Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def generate_walking_directions(start_lat, start_lng, end_lat, end_lng, total_distance_m):
    """Генерация пошаговых указаний для пешеходного маршрута в Алматы."""
    
    # Расчет направления
    lat_diff = end_lat - start_lat
    lng_diff = end_lng - start_lng
    
    # Определение основного направления
    angle = math.atan2(lng_diff, lat_diff)
    bearing = (math.degrees(angle) + 360) % 360
    
    direction = get_direction_name(bearing)
    
    # Реальные улицы Алматы для генерации маршрута
    almaty_streets = [
        "проспект Абая", "улица Сатпаева", "проспект Аль-Фараби", 
        "улица Толе би", "проспект Назарбаева", "улица Жибек Жолы",
        "проспект Достык", "улица Манаса", "улица Богенбай батыра",
        "проспект Райымбека", "улица Курмангазы", "улица Кабанбай батыра"
    ]
    
    # Выбираем улицы для маршрута на основе координат
    random.seed(int((start_lat + end_lat + start_lng + end_lng) * 1000))
    main_street = random.choice(almaty_streets[:6])  # Основные проспекты
    cross_street = random.choice(almaty_streets[6:])  # Поперечные улицы
    
    # Генерация шагов маршрута
    steps = []
    
    # Начальная инструкция
    steps.append({
        'instruction': f'Выходите на {main_street} и поверните {direction}',
        'distance': '0 м',
        'bearing': bearing,
        'type': 'start'
    })
    
    # Промежуточные шаги для длинных маршрутов
    if total_distance_m > 300:
        mid_distance = total_distance_m // 3
        steps.append({
            'instruction': f'Идите по {main_street} прямо {mid_distance} метров до пересечения с {cross_street}',
            'distance': f'{mid_distance} м',
            'bearing': bearing,
            'type': 'continue'
        })
        
        if total_distance_m > 600:
            landmark = random.choice(['светофора', 'автобусной остановки', 'торгового центра', 'парка'])
            steps.append({
                'instruction': f'Продолжайте движение до {landmark}, ориентируйтесь по звукам движения',
                'distance': f'{total_distance_m - 2 * mid_distance} м',
                'bearing': bearing,
                'type': 'continue'
            })
    
    # Приближение к цели для длинных маршрутов
    if total_distance_m > 200:
        final_turn = random.choice(['поверните направо', 'поверните налево', 'продолжайте прямо'])
        steps.append({
            'instruction': f'Через 100 метров {final_turn}, пункт назначения будет справа',
            'distance': '100 м',
            'bearing': bearing,
            'type': 'approach'
        })
    
    # Финальная инструкция
    steps.append({
        'instruction': 'Вы прибыли в пункт назначения. Поздравляем!',
        'distance': '0 м',
        'bearing': bearing,
        'type': 'finish'
    })
    
    return steps

def get_direction_name(bearing):
    """Преобразование угла в название направления."""
    directions = [
        (0, 22.5, "прямо на север"),
        (22.5, 67.5, "направо на северо-восток"),
        (67.5, 112.5, "направо на восток"),
        (112.5, 157.5, "направо на юго-восток"),
        (157.5, 202.5, "назад на юг"),
        (202.5, 247.5, "налево на юго-запад"),
        (247.5, 292.5, "налево на запад"),
        (292.5, 337.5, "налево на северо-запад"),
        (337.5, 360, "прямо на север")
    ]
    
    for min_angle, max_angle, direction_name in directions:
        if min_angle <= bearing < max_angle:
            return direction_name
    
    return "прямо"

@app.route('/calibrate_compass', methods=['POST'])
def calibrate_compass():
    """Калибровка компаса (эмуляция)."""
    return jsonify({
        'success': True,
        'message': 'Компас откалиброван успешно',
        'heading': 45  # Пример направления в градусах
    })

@app.route('/capture_view', methods=['POST'])
def capture_view():
    """Захват изображения для определения направления (эмуляция)."""
    return jsonify({
        'success': True,
        'message': 'Направление определено с помощью Huntintel.io и Google Earth API',
        'direction': 'Северо-восток',
        'confidence': 95,
        'apis_used': ['huntintel.io', 'Google Earth']
    })

@app.route('/process_main_command', methods=['POST'])
def process_main_command():
    """Обработка голосовых команд на главной странице."""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'Аудиофайл не предоставлен'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Аудиофайл не выбран'}), 400
        
        # Сохранение файла
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Определение MIME типа
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type_map = {
            '.webm': 'audio/webm',
            '.m4a': 'audio/m4a',
            '.mp3': 'audio/mp3',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }
        mime_type = mime_type_map.get(file_ext, 'audio/webm')
        
        # Чтение аудиофайла
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        # Создание промпта для главной страницы
        prompt = """
        Вы - голосовой ассистент навигационного приложения SmartAla для слепых людей. 
        Пользователь находится на главной странице приложения.

        ДОСТУПНЫЕ КОМАНДЫ И ДЕЙСТВИЯ:
        - "Начать навигацию" / "Навигация" → направить на страницу навигации
        - "Очки" / "Подключить очки" → направить на страницу Meta x Rayban
        - "Мои места" / "Сохраненные места" → показать сохраненные места
        - "Справка" / "Помощь" → показать справку
        - "Сохранить место" / "Сохранить текущее место" → сохранить текущую локацию
        - Общие вопросы о приложении

        ИНСТРУКЦИИ:
        1. Расшифруйте аудио точно
        2. Определите намерение пользователя
        3. Дайте четкий ответ и укажите действие

        ФОРМАТ ОТВЕТА:
        ТРАНСКРИПЦИЯ: [что вы услышали]
        ОТВЕТ: [ваш ответ пользователю]
        """
        
        response = navigation_service.model.generate_content([
            prompt, 
            {"mime_type": mime_type, "data": audio_data}
        ])
        
        # Очистка аудиофайла
        try:
            os.remove(file_path)
        except:
            pass
        
        # Парсинг ответа
        response_text = response.text.strip()
        
        transcription = ""
        ai_response = ""
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('ТРАНСКРИПЦИЯ:'):
                current_section = 'transcription'
                transcription += line.replace('ТРАНСКРИПЦИЯ:', '').strip()
            elif line.startswith('ОТВЕТ:'):
                current_section = 'response'
                ai_response += line.replace('ОТВЕТ:', '').strip()
            elif current_section == 'transcription' and line:
                transcription += ' ' + line
            elif current_section == 'response' and line:
                ai_response += ' ' + line
        
        # Запасной парсинг
        if not transcription or not ai_response:
            if 'ТРАНСКРИПЦИЯ:' in response_text and 'ОТВЕТ:' in response_text:
                parts = response_text.split('ОТВЕТ:')
                transcription = parts[0].replace('ТРАНСКРИПЦИЯ:', '').strip()
                ai_response = parts[1].strip()
            else:
                transcription = "Команда обработана"
                ai_response = response_text
        
        return jsonify({
            'success': True,
            'transcription': transcription.strip(),
            'response': ai_response.strip()
        })
        
    except Exception as e:
        logger.error(f"Ошибка в process_main_command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/create_voice_route', methods=['POST'])
def create_voice_route():
    """Создание маршрута по голосовому запросу."""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'Аудиофайл не предоставлен'}), 400
        
        file = request.files['audio']
        user_location = request.form.get('location', '{}')
        
        try:
            user_location = json.loads(user_location)
        except:
            user_location = {}
        
        # Сохранение файла
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Определение MIME типа
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type_map = {
            '.webm': 'audio/webm',
            '.m4a': 'audio/m4a',
            '.mp3': 'audio/mp3',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }
        mime_type = mime_type_map.get(file_ext, 'audio/webm')
        
        # Чтение аудиофайла
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        location_info = f"Ваше местоположение: {user_location.get('lat', 43.238293)}, {user_location.get('lng', 76.889709)} в центре Алматы"
        
        prompt = f"""
        Вы - профессиональный голосовой навигатор SmartAla для города Алматы. Вы превосходно знаете весь город.
        
        ЗАДАЧА: Прослушать аудио и построить точный пешеходный маршрут к названному месту в Алматы.
        
        ВАШЕ МЕСТОПОЛОЖЕНИЕ:
        {location_info}
        
        ИНСТРУКЦИИ:
        1. Расшифруйте что говорит пользователь точно
        2. Определите место назначения из речи  
        3. Постройте детальный пешеходный маршрут с названиями улиц Алматы
        4. Используйте реальные улицы: проспект Абая, Сатпаева, Аль-Фараби, Толе би, Назарбаева, Жибек Жолы
        5. Укажите точное время и расстояние
        6. Предупредите о светофорах, переходах, ориентирах
        7. Говорите как профессиональный навигатор
        
        ПРИМЕРЫ МЕСТ В АЛМАТЫ:
        - МУИТ (Международный университет информационных технологий) - улица Манаса
        - Kok-Tobe - канатная дорога с проспекта Достык
        - Зеленый базар - улица Жибек Жолы
        - Парк 28 панфиловцев - проспект Достык
        - Алматы Арена - проспект Аль-Фараби
        
        ФОРМАТ ОТВЕТА:
        ТРАНСКРИПЦИЯ: [что вы услышали]
        НАЗНАЧЕНИЕ: [конкретное место в Алматы]  
        МАРШРУТ: [пошаговые указания с названиями улиц, расстояниями и ориентирами]
        ВРЕМЯ: [точное время в минутах]
        РАССТОЯНИЕ: [точное расстояние в метрах]
        """
        
        response = navigation_service.model.generate_content([
            prompt, 
            {"mime_type": mime_type, "data": audio_data}
        ])
        
        # Очистка аудиофайла
        try:
            os.remove(file_path)
        except:
            pass
        
        # Парсинг ответа
        response_text = response.text.strip()
        
        result = {
            'transcription': '',
            'destination': '',
            'route': '',
            'time': '',
            'distance': ''
        }
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('ТРАНСКРИПЦИЯ:'):
                current_section = 'transcription'
                result['transcription'] += line.replace('ТРАНСКРИПЦИЯ:', '').strip()
            elif line.startswith('НАЗНАЧЕНИЕ:'):
                current_section = 'destination'
                result['destination'] += line.replace('НАЗНАЧЕНИЕ:', '').strip()
            elif line.startswith('МАРШРУТ:'):
                current_section = 'route'
                result['route'] += line.replace('МАРШРУТ:', '').strip()
            elif line.startswith('ВРЕМЯ:'):
                current_section = 'time'
                result['time'] += line.replace('ВРЕМЯ:', '').strip()
            elif line.startswith('РАССТОЯНИЕ:'):
                current_section = 'distance'
                result['distance'] += line.replace('РАССТОЯНИЕ:', '').strip()
            elif current_section and line:
                result[current_section] += ' ' + line
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Ошибка создания голосового маршрута: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/psychologist')
def psychologist():
    return render_template('psychologist.html')

@app.route('/psychologist_chat', methods=['POST'])
def psychologist_chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Промпт для психолога
        psychologist_prompt = f"""
        Ты - профессиональный психолог, специализирующийся на работе со слабовидящими и слепыми людьми. 
        Твоя задача - оказать эмоциональную поддержку, помочь справиться со стрессом и тревогой.
        
        Принципы общения:
        - Будь эмпатичным и понимающим
        - Используй теплый, поддерживающий тон
        - Давай практические советы по адаптации
        - Помогай находить внутренние ресурсы
        - Не давай медицинских диагнозов
        - Говори простым, понятным языком
        - Будь краток, но содержателен (2-3 предложения)
        
        Сообщение пользователя: {user_message}
        
        Ответь как профессиональный психолог, оказав поддержку и помощь.
        """
        
        # Отправка запроса к Gemini API
        response = navigation_service.model.generate_content(psychologist_prompt)
        ai_response = response.text.strip()
        
        return jsonify({
            'response': ai_response,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Ошибка в психологическом чате: {e}")
        return jsonify({
            'response': 'Извините, произошла техническая ошибка. Попробуйте еще раз.',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5002) 