# Спецификация конфигурационного файла схемы (Config Spec)

**Проект:** DataBridge — Конвертер и валидатор данных  
**Форматы конфигурации:** YAML (`.yaml`, `.yml`) или JSON (`.json`)

---

## 1. Общая структура файла конфигурации

Конфигурационный файл состоит из трёх основных секций:
1. `fields` — список правил валидации и трансформаций для каждого поля (обязательная секция).
2. `mapping` — словарь переименования колонок на выходе (опциональная секция).
3. `options` — глобальные параметры конвейера (опциональная секция).

### Пример конфигурации в формате YAML:
```yaml
fields:
  - name: id
    type: integer
    required: true
    unique: true

  - name: name
    type: string
    required: true
    min_length: 2
    max_length: 50
    transformations:
      - strip
      - capitalize

  - name: email
    type: string
    required: true
    pattern: "^[^@]+@[^@]+\\.[^@]+$"
    transformations:
      - strip
      - lower

  - name: age
    type: integer
    min: 16
    max: 100

  - name: birth_date
    type: date
    format: "YYYY-MM-DD"

mapping:
  birth_date: birthday
  email: contact_email
```

### Пример эквивалентной конфигурации в формате JSON:
```json
{
  "fields": [
    {
      "name": "id",
      "type": "integer",
      "required": true,
      "unique": true
    },
    {
      "name": "name",
      "type": "string",
      "required": true,
      "min_length": 2,
      "max_length": 50,
      "transformations": ["strip", "capitalize"]
    },
    {
      "name": "email",
      "type": "string",
      "required": true,
      "pattern": "^[^@]+@[^@]+\\.[^@]+$",
      "transformations": ["strip", "lower"]
    },
    {
      "name": "age",
      "type": "integer",
      "min": 16,
      "max": 100
    },
    {
      "name": "birth_date",
      "type": "date",
      "format": "YYYY-MM-DD"
    }
  ],
  "mapping": {
    "birth_date": "birthday",
    "email": "contact_email"
  }
}
```

---

## 2. Спецификация параметров поля (`FieldRule`)

| Параметр | Тип | Обязательный | Описание | Пример |
|---|---|---|---|---|
| `name` | `string` | **Да** | Имя колонки во входных данных | `name: "email"` |
| `type` | `string` | Нет | Ожидаемый тип данных: `integer`, `float`, `string`, `date`, `boolean` | `type: integer` |
| `required` | `boolean` | Нет | Обязательность присутствия непустого значения (по умолчанию `false`) | `required: true` |
| `unique` | `boolean` | Нет | Проверка уникальности значений поля среди всех строк выборки | `unique: true` |
| `min` | `number` / `date` | Нет | Минимальное допустимое значение (включительно) | `min: 16` |
| `max` | `number` / `date` | Нет | Максимальное допустимое значение (включительно) | `max: 100` |
| `min_length` | `integer` | Нет | Минимальная длина строки | `min_length: 2` |
| `max_length` | `integer` | Нет | Максимальная длина строки | `max_length: 100` |
| `pattern` | `string` | Нет | Регулярное выражение (RegEx) для валидации строки | `pattern: "^\\+?[0-9]{10,15}$"` |
| `format` | `string` | Нет | Шаблон даты (для `type: date`): `YYYY-MM-DD`, `DD.MM.YYYY`, `DD/MM/YYYY` | `format: "YYYY-MM-DD"` |
| `allowed_values` | `list` | Нет | Список допустимых фиксированных значений (enum) | `allowed_values: ["active", "pending"]` |
| `alias` | `string` | Нет | Новое имя поля при экспорте (альтернатива секции `mapping`) | `alias: "user_email"` |
| `transformations` | `list` | Нет | Список трансформаций, применяемых к полю перед записью | `transformations: [strip, lower]` |

---

## 3. Справочник трансформаций (`transformations`)

Трансформации выполняются последовательно для валидных записей:

1. **`upper`** / **`uppercase`**: Перевод текста в верхний регистр (`"иван"` → `"ИВАН"`).
2. **`lower`** / **`lowercase`**: Перевод текста в нижний регистр (`"IVAN@MAIL.RU"` → `"ivan@mail.ru"`).
3. **`strip`** / **`trim`**: Удаление начальных и завершающих пробелов (`"  text  "` → `"text"`).
4. **`capitalize`**: Первая буква заглавная (`"москва"` → `"Москва"`).
5. **`replace_map`** / **`dict_replace`**: Замена значений по словарю:
   ```yaml
   transformations:
     - name: replace_map
       mapping:
         "М": "Мужской"
         "Ж": "Женский"
       default: "Не указан"
   ```
6. **`timestamp_to_date`**: Преобразование Unix timestamp (секунды или миллисекунды) в дату:
   ```yaml
   transformations:
     - name: timestamp_to_date
       output_format: "YYYY-MM-DD"
   ```
7. **`format_date`**: Изменение формата даты (например, из `15.01.1999` в `1999-01-15`):
   ```yaml
   transformations:
     - name: format_date
       input_format: "DD.MM.YYYY"
       output_format: "YYYY-MM-DD"
   ```
8. **`default`**: Подстановка значения по умолчанию при пустом поле:
   ```yaml
   transformations:
     - name: default
       default_value: "Не указано"
   ```

---

## 4. Секция переименования (`mapping`)

Позволяет централизованно задать соответствие имен входных колонок именам колонок в результирующем файле:
```yaml
mapping:
  старое_имя: новое_имя
  birth_date: birthday
  email: contact_email
```
Если колонка не указана в секции `mapping` и для неё не задан `alias`, её имя сохраняется без изменений.
