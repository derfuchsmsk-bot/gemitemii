# Список задач по исправлению критических проблем

## Архитектурные и инфраструктурные задач

### 1. Webhook Security (Критический)
**Файл**: `main.py`
- [x] Добавить валидацию `X-Telegram-Bot-Api-Secret-Token` в webhook endpoint
- [ ] Реализовать проверку IP-адресов Telegram (если возможно)
- [x] Добавить middleware для безопасности webhook (реализовано через FastAPI Header)

### 2. State Management (Критический)
**Файлы**: `src/settings_store.py`, `src/handlers/chat.py`
- [x] Заменить `MemoryStorage` на Redis или Firestore (Firestore реализован для настроек)
- [x] Переписать глобальные словари `USER_SETTINGS` и `CONTEXT` на постоянное хранилище
- [x] Убедиться в состоянии персистентности при масштабировании Cloud Run

### 3. Docker Configuration
**Файл**: `Dockerfile`
- [ ] Добавить аргументы для отладки (development vs production)
- [x] Добавить health check endpoint в контейнер
- [x] Убедиться в правильной конфигурации вебхуков для Cloud Run (авто-настройка при старте)

## Бизнес-логика и обработчики

### 4. Обработчик `img_edit` (Критический)
**Файл**: `src/handlers/image_gen.py`
- [x] Реализовать обработчик для callback `img_edit`
- [x] Добавить логику редактирования изображений
- [x] Обновить клавиатуру с кнопкой редактирования

### 5. Синхронизация callback data (Важный)
**Файлы**: `src/handlers/settings.py`, `src/keyboards/image_gen_kbs.py`
- [x] Унифицировать callback data (English только)
- [x] Заменить `gen_set_style_Фотореализм` на `gen_set_style_photo`
- [x] Исправить обработку в `image_gen.py` для работы с английским callback
- [x] Удалить русские строки из callback data

### 6. Модель "Модель" (Dead Code)
**Файл**: `src/handlers/settings.py`
- [x] Либо добавить обработчик для `settings_model` callback
- [ ] Либо удалить кнопку "Model" из `settings_kbs.py`

## Безопасность и производительность

### 7. Rate Limiting
**Файлы**: `src/handlers/chat.py`, `src/handlers/image_gen.py`
- [x] Добавить middleware для ограничения запросов (RateLimitMiddleware добавлен)
- [ ] Реализовать очередь запросов к Vertex AI
- [x] Добавить ограничения на частоту для предотвращения DDoS

### 8. Error Handling
**Файлы**: Все обработчики
- [x] Скрыть внутренние ошибки от пользователей (stack traces)
- [x] Добавить логирование ошибок в Cloud Logging (через logger)
- [x] Реализовать пользовательские сообщения об ошибках

### 9. Secret Management
**Файл**: `src/config.py`
- [ ] Проверить валидацию `GOOGLE_APPLICATION_CREDENTIALS`
- [x] Добавить проверку обязательности переменных окружения
- [ ] Добавить обработку путей к JSON ключам

## Интеграция Vertex AI

### 10. Model Availability
**Файл**: `src/services/vertex_ai.py`
- [x] Проверить доступность `gemini-3-pro-image-preview` в `us-central1`
- [ ] Добавить fallback на `us-east1` если недоступно
- [ ] Проверить поддержку Image Generation API в выбранной локации

### 11. Timeout Handling
**Файл**: `src/services/vertex_ai.py`
- [x] Добавить таймауты на `await` вызовы
- [x] Реализовать retry логику с exponential backoff
- [x] Добавить ограничение на время выполнения генерации

## UI/UX и обработка данных

### 12. File ID Persistence
**Файл**: `src/handlers/image_gen.py`
- [x] Обработать expire file_id (добавить повторную загрузку)
- [ ] Добавить кэширование загруженных файлов
- [x] Реализовать проверку существования file_id

### 13. Prompt Engineering
**Файлы**: `src/handlers/image_gen.py`, `src/services/vertex_ai.py`
- [ ] Убрать жестко закодированные английские инструкции
- [ ] Поддержать мультиязычность (русский + английский)
- [x] Исправить логику переключения "Magic Prompt" vs regular prompt

## Технический долг

### 14. Dead Code Cleanup
**Файл**: `src/bot.py`
- [ ] Решить судьбу `src/bot.py` (удалить или поддерживать polling mode)
- [ ] Удалить или переписать `main()` функцию в `bot.py`
- [ ] Добавить флаг/аргумент командной строки для выбора режима

### 15. Dependency Management
**Файл**: `requirements.txt` (или pyproject.toml)
- [ ] Проверить совместимость `google-cloud-aiplatform` с `pydantic 2.x`
- [x] Обновить версии зависимостей до стабильных
- [x] Добавить проверку зависимостей в CI/CD (добавлена firestore библиотека)

### 16. Модульное тестирование
- [ ] Создать тесты для webhook валидации
- [ ] Написать тесты для валидации callback data
- [ ] Добавить тесты для Vertex AI integration

## Документация

### 17. Configuration Documentation
**Файл**: `README.md` или `.env.example`
- [ ] Добавить список всех необходимых переменных окружения
- [ ] Описать процесс настройки Google Cloud
- [ ] Добавить инструкцию по созданию Telegram Secret Token

### 18. Architecture Documentation
- [ ] Описать flow данных (от webhook до Vertex AI)
- [ ] Документировать схему состояний FSM
- [ ] Описать схему хранения данных (Redis/Firestore)

## Cloud Run Configuration

### 19. Webhook Setup Automation
**Файл**: `main.py` (startup logic)
- [x] Добавить логику автоматической настройки webhook при старте
- [x] Проверить формат WEBHOOK_URL (должен включать /webhook)
- [x] Добавить перерегистрацию webhook при изменении URL

### 20. Health Check
**Файл**: `main.py`
- [x] Добавить endpoint `/health` для Cloud Run
- [x] Реализовать проверку подключения к Vertex AI
- [x] Добавить readiness/liveness проверки

## Приоритетность выполнения

### Критические (Critical - блокируют production)
1. **Webhook Security** (Задача 1)
2. **State Management** (Задача 2)
3. **img_edit Handler** (Задача 4)

### Высокие (High - важны для функциональности)
4. **Callback Data Unification** (Задача 5)
5. **Rate Limiting** (Задача 7)
6. **Error Handling** (Задача 8)

### Средние (Medium - улучшения и оптимизация)
7. **Timeout Handling** (Задача 11)
8. **Prompt Engineering** (Задача 13)
9. **File ID Persistence** (Задача 12)

### Низкие (Low - технический долг)
10. **Dead Code Cleanup** (Задача 14)
11. **Documentation** (Задачи 17-18)
12. **Testing** (Задача 16)

## Временная оценка

- **Критические задачи**: 8-12 часов
- **Высокие задачи**: 6-8 часов
- **Средние задачи**: 4-6 часов
- **Низкие задачи**: 4-6 часов

**Общее время**: ~22-32 часа для полного исправления

## Зависимости между задачами

```
Задача 1 (Webhook) ─┐
Задача 2 (Storage) ─┼───> Задача 16 (Тесты)
Задача 7 (Limiting) ┘
        │
        ▼
Задача 5 (Callbacks) ─┐
Задача 4 (img_edit) ──┼───> Задача 13 (Prompts)
Задача 8 (Errors) ────┘
        │
        ▼
Задача 10 (Models) ─┐
Задача 11 (Timeout) ┘
```

## Проверка после исправлений

- [ ] Webhook отвечает с валидным токеном
- [ ] Состояния сохраняются между рестартами контейнера
- [ ] Все callback кнопки работают
- [ ] Ошибки не раскрывают внутреннюю информацию
- [ ] Rate limiting работает
- [ ] Vertex AI запросы выполняются с таймаутами
- [ ] Docker контейнер запускается без ошибок
- [ ] Cloud Run health check возвращает 200
