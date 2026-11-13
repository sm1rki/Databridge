# DataBridge — Универсальный конвертер и валидатор данных

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-36%20passed-success.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Pipeline-blueviolet.svg)](DOCS/Architecture.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Групповой учебный проект** по дисциплине «Программная инженерия»  
> **Срок защиты:** ноябрь 2026 г.

---

## 1. Описание проекта

В учебных отделах университетов и компаниях малого бизнеса данные регулярно поступают в несовместимых форматах: выгрузки CSV с произвольными разделителями, JSON-дампы, XML-выгрузки и таблицы Excel (.xlsx). Ручная сверка и чистка таких данных отнимает много времени и приводит к ошибкам при загрузке в основные учетные системы.

**DataBridge** — это специализированная консольная утилита (CLI) для автоматической обработки табличных данных:
- Читает данные из любого из 4 форматов (CSV, JSON, XML, Excel);
- Валидирует каждую запись по строгим декларативным правилам (YAML/JSON схема);
- Автоматически изолирует некорректные записи в отдельный файл `errors.csv`;
- Трансформирует значения (регистр, обрезка пробелов, справочники, даты);
- Выполняет маппинг (переименование) полей;
- Сохраняет результат в любой выбранный целевой формат;
- Формирует понятный консольный отчёт и интерактивный **HTML-отчёт**.

> **Важно:** Это инструмент обработки данных (ETL/Data Pipeline). Базы данных не используются — только потоковая и пакетная обработка файлов.

---

## 2. Архитектура и структура модулей

Проект спроектирован по модульному принципу согласно **SOLID** и шаблону **Pipeline Pattern**:

```text
FormatConverter/
├── databridge/                 # Основной пакет утилиты
│   ├── readers/                # Модули чтения данных (CSV, JSON, XML, Excel, Factory)
│   ├── writers/                # Модули записи данных (CSV, JSON, XML, Excel, Factory)
│   ├── validators/             # Движок валидации, правила, модели
│   ├── converters/             # Конвейер, трансформации, маппер колонок
│   ├── reporters/              # Консольные, HTML и аналитические отчёты
│   └── cli/                    # Парсер аргументов командной строки и обработчики
├── tests/                      # Модульные и интеграционные тесты (36 тестов)
├── samples/                    # Тестовые данные (валидные, с ошибками, схемы)
├── presentation/               # Интерактивная презентация к защите (HTML + MD)
├── DOCS/                       # Полный комплект технической документации
│   ├── Requirements.md         # Функциональные и нефункциональные требования
│   ├── Architecture.md         # Описание архитектуры и диаграммы (Mermaid)
│   ├── Config_Spec.md          # Спецификация файла правил валидации
│   ├── Usage_Guide.md          # Сценарии использования с примерами
│   ├── Test_Plan.md            # План тестирования (25 сценариев)
│   ├── Test_Report.md          # Отчёт о результатах тестирования
│   └── User_Manual.md          # Полное руководство пользователя
├── FormatConverter.py          # Точка входа для Visual Studio и прямого запуска
├── DEFENSE_QA.md               # Ответы на 10 контрольных вопросов к защите
├── TEAM.md                     # Роли в команде
├── CONTRIBUTIONS.md            # Вклад каждого участника
├── requirements.txt            # Зависимости проекта
└── setup.py                    # Скрипт сборки и регистрации CLI команды
```

---

## 3. Быстрый старт

### 3.1. Установка
```bash
# 1. Клонировать или открыть каталог проекта
cd FormatConverter

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Установить утилиту в систему
pip install -e .
```

*После установки становится доступна глобальная команда `databridge`.* Также запуск возможен через:
```bash
python FormatConverter.py <команда>
```

---

## 4. Основные команды CLI

### 4.1. Конвертация данных с валидацией
```bash
databridge convert samples/invalid.csv --to json --config samples/schema.yaml --output output.json --report report.html
```

**Пример консольного вывода:**
```text
Всего записей: 12
Успешно обработано: 1
Ошибок: 11
  - Строка 3: поле "email" не соответствует формату
  - Строка 4: поле "age" вне диапазона (200 > max 100)
  - Строка 5: поле "name" обязательное поле отсутствует или пусто
  - Строка 6: поле "age" не является целым числом (integer): 'abc'
  - Строка 7: поле "id" значение '1' не уникально (уже встречалось ранее)
  - Строка 8: поле "name" длина строки (1) меньше минимальной (2)
  - Строка 9: поле "birth_date" не соответствует формату даты (ожидался формат YYYY-MM-DD): '99-99-9999'
  - Строка 10: поле "id" обязательное поле отсутствует или пусто
  - Строка 11: поле "age" меньше минимума (16)
  - Строка 12: поле "email" обязательное поле отсутствует или пусто
  - Строка 13: поле "email" не соответствует формату
Результат сохранён: output.json
Ошибки сохранены: errors.csv
Отчёт сохранён: report.html
```

### 4.2. Проверка данных (валидация)
```bash
databridge validate samples/valid.csv --config samples/schema.yaml
```

### 4.3. Анализ структуры и профилирование файла
```bash
databridge stats samples/valid.csv
```

---

## 5. Конфигурация схемы (YAML / JSON)

Схема валидации позволяет гибко настраивать типы данных, проверки и маппинг:

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

Подробное описание параметров доступно в [DOCS/Config_Spec.md](DOCS/Config_Spec.md).

---

## 6. Запуск тестов

Проект покрыт 36 модульными и интеграционными тестами:
```bash
pytest -v
```

Все тесты выполняются менее чем за 3 секунды со 100% успехом.

---

## 7. Комплект документации к защите

1. [DOCS/Requirements.md](DOCS/Requirements.md) — Функциональные и нефункциональные требования
2. [DOCS/Architecture.md](DOCS/Architecture.md) — Архитектурная спецификация и диаграммы
3. [DOCS/Config_Spec.md](DOCS/Config_Spec.md) — Спецификация конфигурационного файла
4. [DOCS/Usage_Guide.md](DOCS/Usage_Guide.md) — Сценарии практического использования
5. [DOCS/Test_Plan.md](DOCS/Test_Plan.md) — План тестирования (25 сценариев)
6. [DOCS/Test_Report.md](DOCS/Test_Report.md) — Отчёт о результатах тестирования
7. [DOCS/User_Manual.md](DOCS/User_Manual.md) — Руководство пользователя
8. [DEFENSE_QA.md](DEFENSE_QA.md) — Ответы на 10 контрольных вопросов к защите
9. [TEAM.md](TEAM.md) — Роли участников команды
10. [CONTRIBUTIONS.md](CONTRIBUTIONS.md) — Вклад участников в разработку
11. [presentation/index.html](presentation/index.html) — Интерактивная веб-презентация к защите (10 слайдов)
