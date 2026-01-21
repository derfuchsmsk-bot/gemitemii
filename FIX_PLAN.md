# План исправлений для восстановления генерации изображений

## 1. Диагностика проблемы: Почему не генерируются изображения?

### Основная причина: Некорректные имена моделей
В файле `src/services/vertex_ai.py` используются несуществующие имена моделей:
- `gemini-3-flash-preview`
- `gemini-3-pro-preview`
- `gemini-3-pro-image-preview`

На данный момент (2024-2025) актуальными версиями являются семейство **Gemini 1.5** (Flash/Pro) и **Gemini 2.0** (Flash Experimental). Для генерации изображений через Vertex AI обычно используется модель **Imagen 3** (`imagen-3.0-generate-001`). Прямая генерация изображений через класс `GenerativeModel` с именем `gemini-3...` невозможна, так как таких моделей нет в публичном доступе Google Cloud.

### Второстепенная причина: Конфигурация региона
В `src/config.py` по умолчанию `REGION = "global"`.
Для работы с Generative AI в Vertex AI часто требуется указать конкретный регион (например, `us-central1`), так как глобальная конечная точка может не поддерживать все функции SDK или требовать другой настройки `api_endpoint`.

### Потенциальная проблема: Rate Limiting
В `main.py` подключен `RateLimitMiddleware(limit=1.0)`. Это может мешать пользователю быстро отправлять промпт после нажатия кнопки меню.

## 2. Структура исправлений

### Шаг 1: Обновление `src/services/vertex_ai.py`
Необходимо заменить инициализацию моделей на актуальные.

**Было:**
```python
self.flash_model = GenerativeModel("gemini-3-flash-preview") 
self.pro_model = GenerativeModel("gemini-3-pro-preview")
self.image_model = GenerativeModel("gemini-3-pro-image-preview")
```

**Станет (Пример):**
```python
# Использовать Imagen 3 для изображений
from vertexai.preview.vision_models import ImageGenerationModel

# ...
self.flash_model = GenerativeModel("gemini-1.5-flash-002") 
self.pro_model = GenerativeModel("gemini-1.5-pro-002")
# Для картинок используем ImageGenerationModel, так как интерфейс GenerativeModel для картинок отличается
self.image_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
```
*Примечание: При смене класса модели потребуется адаптировать метод `generate_image`, так как `ImageGenerationModel` имеет другой метод вызова (`generate_images` вместо `generate_content`).*

### Шаг 2: Доработка `main.py`
Файл `main.py` отвечает за запуск и конфигурацию. В нем нужно:
1.  **Улучшить проверку переменных окружения**: При старте проверять наличие `PROJECT_ID` и валидность `REGION`.
2.  **Скорректировать Middleware**: Увеличить лимит или исключить определенные действия.
3.  **Логирование**: Добавить вывод текущей конфигурации (без секретов) при старте для отладки.

### Шаг 3: Исправление `src/handlers/image_gen.py`
Так как мы меняем логику вызова модели (с `GenerativeModel` на `ImageGenerationModel` или правильный вызов Gemini), нужно убедиться, что хендлер корректно обрабатывает возвращаемый результат (объект изображения).

## 3. План действий (Checklist)

1.  [ ] **Изменить `src/services/vertex_ai.py`**:
    *   Использовать `ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")`.
    *   Переписать метод `generate_image` под API Imagen 3.
    *   Обновить текстовые модели на `gemini-1.5-flash`.
2.  [ ] **Обновить `src/config.py`**:
    *   Установить дефолтный регион `us-central1` (наиболее стабильный для GenAI).
3.  [ ] **Оптимизировать `main.py`**:
    *   Добавить `lifespan` для управления ресурсами (вместо устаревшего `@app.on_event("startup")`).
    *   Ослабить `RateLimitMiddleware` (например, до 0.5-0.7 сек или убрать для тестов).

Этот файл служит основой для внесения изменений.
