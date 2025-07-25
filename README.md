# SmartAla - Умная Навигационная Система для Слепых

![SmartAla Logo](https://img.shields.io/badge/SmartAla-Navigation%20for%20Blind-blue?style=for-the-badge&logo=compass)

**SmartAla** - это инновационная веб-платформа для навигации, специально разработанная для помощи слепым и слабовидящим людям в перемещении по городу. Система использует передовые технологии искусственного интеллекта, голосовое управление и интеграцию с современными устройствами.

## 🌟 Основные возможности

### 🧭 Интеллектуальная навигация
- **Калибровка компаса** с автоматическим звуковым сопровождением
- **Определение направления** через камеру с использованием API Huntintel.io и Google Earth
- **Геолокация** для точного определения текущего местоположения
- **Интеграция Google Maps** для построения оптимальных маршрутов

### 🎤 Голосовой ассистент на базе Gemini AI
- Обработка голосовых команд на русском языке
- Пошаговые навигационные указания
- Консультации по правильности направления движения
- История разговоров для контекста

### 📍 Сохранение и обмен локациями
- **Статические ссылки** для сохраненных мест
- Автоматическое определение геолокации при переходе по ссылке
- Построение маршрута к сохраненной точке
- Простой обмен местами через URL

### 🥽 Поддержка Meta x Rayban Smart Glasses
- Симуляция подключения умных очков
- Визуальная навигация в поле зрения
- Распознавание объектов и препятствий
- Голосовые команды без использования рук

### ♿ Полная доступность
- Оптимизация для скрин-ридеров
- Высококонтрастный интерфейс
- Крупные шрифты и элементы управления
- Полная навигация с клавиатуры
- ARIA-разметка для всех элементов

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- Современный веб-браузер с поддержкой микрофона
- API-ключ Google Gemini

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd IITU_SmartAla_V2
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте переменные окружения:**
Создайте файл `.env` в корневой папке:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

4. **Запустите приложение:**
```bash
python app.py
```

5. **Откройте в браузере:**
```
http://127.0.0.1:5000
```

## 📱 Использование

### Основные страницы

#### 🏠 Главная страница (`/`)
- Навигационные карточки для доступа к функциям
- Сохранение текущего местоположения
- Голосовые команды для навигации по сайту
- Управление сохраненными местами

#### 🧭 Навигация (`/navigate`)
- Калибровка компаса устройства
- Определение направления взгляда
- Голосовой ассистент для навигации
- Отображение текущего статуса системы

#### 🥽 Meta x Rayban Glasses (`/glasses`)
- Симуляция поиска и подключения очков
- Управление функциями умных очков
- Настройки яркости и звука
- Журнал активности подключения

#### 📍 Сохраненные места (`/location/<id>`)
- Автоматический переход к навигации
- Загрузка данных сохраненного места
- Построение маршрута к точке назначения

### Голосовые команды

#### На главной странице:
- "Начать навигацию" - переход к навигации
- "Подключить очки" - переход к управлению очками  
- "Мои места" - управление сохраненными местами
- "Справка" - показать инструкции
- "Сохранить место" - сохранить текущую локацию

#### На странице навигации:
- "Куда мне идти?" - получить направление
- "Где я нахожусь?" - узнать местоположение
- "Повторить маршрут" - повторить указания
- "Сохранить это место" - сохранить текущую точку

### Клавиатурное управление
- `Tab` - навигация между элементами
- `Enter/Space` - активация элемента  
- `Escape` - отмена записи голоса

## 🔧 Архитектура

### Backend (Flask)
```
app.py - Основное приложение Flask
├── GeminiNavigationService - Сервис обработки голоса
├── Маршруты навигации
├── API для работы с локациями
└── Интеграция с внешними API
```

### Frontend
```
templates/
├── base.html - Базовый шаблон с доступностью
├── index.html - Главная страница
├── navigate.html - Интерфейс навигации
└── glasses.html - Управление очками
```

### Ключевые технологии
- **Flask** - веб-фреймворк
- **Google Gemini AI** - обработка голоса и навигация
- **Web Speech API** - синтез речи
- **Geolocation API** - определение местоположения
- **Device Orientation** - работа с компасом
- **MediaRecorder API** - запись аудио

## 🔌 API интеграции

### Реализованные API
- ✅ **Google Gemini** - голосовой ассистент и навигация
- ✅ **Geolocation API** - определение местоположения
- ✅ **Device Orientation** - компас устройства

### Симулированные API (для демонстрации)
- 🔄 **Huntintel.io** - анализ изображения для направления
- 🔄 **Google Earth** - определение ориентиров
- 🔄 **Google Maps** - построение маршрутов
- 🔄 **Meta x Rayban** - подключение умных очков

## 🛡️ Безопасность и конфиденциальность

- Аудиофайлы автоматически удаляются после обработки
- Геолокация используется только с согласия пользователя
- История разговоров ограничена последними 50 сообщениями
- Все данные обрабатываются локально (кроме AI-запросов)

## 🌐 Поддерживаемые языки

- 🇷🇺 Русский (основной)
- 🇺🇸 English (планируется)
- 🇰🇿 Қазақша (планируется)

## 🤝 Участие в разработке

Этот проект создан в рамках хакатона для решения задач навигации слепых людей в городской среде.

### Планы развития
- [ ] Интеграция с реальным Google Maps API
- [ ] Реальная поддержка Meta x Rayban очков
- [ ] Офлайн-режим работы
- [ ] Мобильное приложение
- [ ] Поддержка общественного транспорта
- [ ] Интеграция с городскими системами

## 📄 Лицензия

Проект создан для образовательных целей и участия в хакатоне.

## 🆘 Поддержка

При возникновении проблем:
1. Убедитесь, что микрофон разрешен в браузере
2. Проверьте API-ключ Google Gemini
3. Убедитесь, что геолокация включена
4. Используйте современный браузер с поддержкой Web APIs

---

**SmartAla** - Делаем город доступным для каждого! 🌟 