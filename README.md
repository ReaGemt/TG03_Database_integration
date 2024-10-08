# Telegram Бот для Сбора Информации о Студентах

Данный Telegram-бот собирает информацию о студентах: имя, возраст и класс, в котором они учатся. Введённые данные сохраняются в базу данных SQLite (`school_data.db`).

## Функциональность

- **Сбор данных**: бот последовательно запрашивает имя, возраст и класс у пользователя.
- **Сохранение данных**: введённая информация сохраняется в базе данных.
- **Личный кабинет**:
  - `/profile` — просмотр сохранённых данных.
  - `/update` — обновление данных.
  - `/delete` — удаление данных.
- **Команды помощи**:
  - `/start` — начало работы с ботом.
  - `/help` — отображение доступных команд.

## Установка

### Требования

- **Python** версии **3.6** или выше.
- Установленные зависимости из файла `requirements.txt`.

### Шаги установки

1. **Клонируйте репозиторий или скачайте файлы проекта** в вашу рабочую директорию.
2. **Установите зависимости из файла requirements.txt**. 

```
pip install -r requirements.txt
```
3. **Создайте бота в Telegram через @BotFather и получите токен API:**
```
    Откройте чат с @BotFather.
    Отправьте команду /newbot и следуйте инструкциям.
    После создания бота вы получите токен в формате 123456789:ABCDEF....
```
4. **Создайте файл config.py в корневой директории проекта и добавьте в него токен бота:**

```
TOKEN = 'ВАШ_ТОКЕН_БОТА'

    Важно: Никогда не публикуйте свой токен бота в открытом доступе.
```

5. **Запустите бота:**

```
    python main.py
```
    

6. **Использование**
```
    Начало работы: найдите вашего бота в Telegram и отправьте команду /start.
    Следуйте инструкциям бота для ввода имени, возраста и класса.
    Управление данными:
        /profile — просмотр ваших данных.
        /update — обновление данных.
        /delete — удаление данных.
    Помощь: используйте команду /help для получения списка доступных команд.
```
- Структура проекта
```
    main.py — основной файл с кодом бота.
    config.py — файл конфигурации с токеном бота.
    requirements.txt — файл с зависимостями проекта.
    school_data.db — база данных SQLite (создаётся автоматически при первом запуске бота).
```
- Команды бота
```
    /start — начать ввод данных.
    /profile — посмотреть сохранённые данные.
    /update — обновить данные.
    /delete — удалить данные.
    /help — показать справку по командам.
    /cancel — отменить текущее действие.
```
7. **Примечания**
```
    База данных: файл school_data.db создаётся автоматически и хранит информацию о пользователях.
    Хранилище состояний: используется MemoryStorage, поэтому при перезапуске бота текущие состояния пользователей будут сброшены.
    Безопасность: убедитесь, что файл config.py не попадает в публичные репозитории или доступ к нему ограничен.
```