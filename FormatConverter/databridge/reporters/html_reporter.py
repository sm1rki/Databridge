"""HTML Reporter for DataBridge validation and conversion results."""

import html
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from ..validators.engine import ValidationResult


class HTMLReporter:
    """Generates self-contained HTML report with summary cards, tables, and analytics."""

    def generate(
        self,
        output_path: str,
        input_file: str,
        output_file: Optional[str] = None,
        errors_file: Optional[str] = None,
        config_file: Optional[str] = None,
        validation_result: Optional[ValidationResult] = None,
        total_records: int = 0,
        valid_records: int = 0,
        error_records: int = 0,
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if validation_result:
            total_records = validation_result.total_count
            valid_records = validation_result.valid_count
            error_records = validation_result.error_count
            errors = validation_result.errors
            field_counts = validation_result.field_error_counts
            rule_counts = validation_result.rule_error_counts
        else:
            errors = []
            field_counts = {}
            rule_counts = {}

        success_rate = (valid_records / total_records * 100) if total_records > 0 else 100.0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build error rows HTML
        error_rows_html = []
        for err in errors:
            val_escaped = html.escape(str(err.value) if err.value is not None else "")
            fld_escaped = html.escape(str(err.field))
            msg_escaped = html.escape(str(err.message))
            rule_escaped = html.escape(str(err.rule))

            error_rows_html.append(
                f"""<tr>
                    <td class="center font-mono">{err.row_number}</td>
                    <td><span class="badge badge-field">{fld_escaped}</span></td>
                    <td class="font-mono text-muted">{val_escaped if val_escaped else "<em>&lt;пусто&gt;</em>"}</td>
                    <td><span class="badge badge-rule">{rule_escaped}</span></td>
                    <td class="text-danger">{msg_escaped}</td>
                </tr>"""
            )

        # Build breakdown rows
        field_stats_html = "".join(
            f"<tr><td>{html.escape(k)}</td><td class='right font-bold text-danger'>{v}</td></tr>"
            for k, v in sorted(field_counts.items(), key=lambda x: -x[1])
        ) or "<tr><td colspan='2' class='text-muted center'>Ошибок по полям нет</td></tr>"

        rule_stats_html = "".join(
            f"<tr><td>{html.escape(k)}</td><td class='right font-bold text-danger'>{v}</td></tr>"
            for k, v in sorted(rule_counts.items(), key=lambda x: -x[1])
        ) or "<tr><td colspan='2' class='text-muted center'>Ошибок по правилам нет</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataBridge - Отчёт о валидации данных</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #1e293b;
            --text-muted: #64748b;
            --primary: #2563eb;
            --success: #16a34a;
            --danger: #dc2626;
            --warning: #d97706;
            --border-color: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            background: var(--card-bg);
            padding: 24px 32px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 6px solid var(--primary);
        }}
        header h1 {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
        header p {{ font-size: 13px; color: var(--text-muted); }}
        
        .meta-bar {{
            background: var(--card-bg);
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            font-size: 13px;
        }}
        .meta-item strong {{ color: var(--text-muted); display: block; font-size: 11px; text-transform: uppercase; }}

        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            border: 1px solid var(--border-color);
        }}
        .stat-title {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }}
        .stat-value {{ font-size: 32px; font-weight: 800; margin-top: 8px; }}
        .stat-card.total .stat-value {{ color: var(--primary); }}
        .stat-card.valid .stat-value {{ color: var(--success); }}
        .stat-card.error .stat-value {{ color: var(--danger); }}
        .stat-card.rate .stat-value {{ color: {"var(--success)" if success_rate >= 90 else ("var(--warning)" if success_rate >= 60 else "var(--danger)")}; }}

        .stats-breakdown {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}
        @media (max-width: 768px) {{
            .stats-breakdown {{ grid-template-columns: 1fr; }}
            header {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
        }}

        .panel {{
            background: var(--card-bg);
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            border: 1px solid var(--border-color);
            overflow: hidden;
            margin-bottom: 24px;
        }}
        .panel-header {{
            padding: 16px 20px;
            font-weight: 700;
            font-size: 16px;
            background: #fafafa;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }}
        th {{ background: #f1f5f9; font-weight: 600; color: #475569; font-size: 12px; text-transform: uppercase; }}
        tr:hover td {{ background: #f8fafc; }}

        .center {{ text-align: center; }}
        .right {{ text-align: right; }}
        .font-mono {{ font-family: Consolas, Monaco, "Courier New", monospace; }}
        .font-bold {{ font-weight: 700; }}
        .text-danger {{ color: var(--danger); }}
        .text-muted {{ color: var(--text-muted); }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-field {{ background: #e0f2fe; color: #0369a1; }}
        .badge-rule {{ background: #fef3c7; color: #92400e; }}

        footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
            padding: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>DataBridge &mdash; Сводный отчёт валидации</h1>
                <p>Автоматизированная проверка и преобразование данных</p>
            </div>
            <div>
                <span class="text-muted font-mono">{now_str}</span>
            </div>
        </header>

        <div class="meta-bar">
            <div class="meta-item">
                <strong>Входной файл</strong>
                <span>{html.escape(input_file)}</span>
            </div>
            <div class="meta-item">
                <strong>Конфигурация</strong>
                <span>{html.escape(config_file or "Не указана")}</span>
            </div>
            <div class="meta-item">
                <strong>Файл результата</strong>
                <span>{html.escape(output_file or "Не сохранялся")}</span>
            </div>
            <div class="meta-item">
                <strong>Файл с ошибками</strong>
                <span>{html.escape(errors_file or "Нет ошибок")}</span>
            </div>
        </div>

        <div class="cards-grid">
            <div class="stat-card total">
                <div class="stat-title">Всего записей</div>
                <div class="stat-value">{total_records}</div>
            </div>
            <div class="stat-card valid">
                <div class="stat-title">Успешно</div>
                <div class="stat-value">{valid_records}</div>
            </div>
            <div class="stat-card error">
                <div class="stat-title">Ошибок</div>
                <div class="stat-value">{error_records}</div>
            </div>
            <div class="stat-card rate">
                <div class="stat-title">Качество данных</div>
                <div class="stat-value">{success_rate:.1f}%</div>
            </div>
        </div>

        <div class="stats-breakdown">
            <div class="panel">
                <div class="panel-header">Ошибки по полям</div>
                <table>
                    <thead>
                        <tr><th>Поле</th><th class="right">Кол-во</th></tr>
                    </thead>
                    <tbody>
                        {field_stats_html}
                    </tbody>
                </table>
            </div>

            <div class="panel">
                <div class="panel-header">Ошибки по типам правил</div>
                <table>
                    <thead>
                        <tr><th>Тип проверки</th><th class="right">Кол-во</th></tr>
                    </thead>
                    <tbody>
                        {rule_stats_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span>Журнал ошибок</span>
                <span class="badge badge-rule">{len(errors)} записей</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th class="center" style="width: 70px;">Строка</th>
                        <th style="width: 140px;">Поле</th>
                        <th style="width: 160px;">Исходное значение</th>
                        <th style="width: 120px;">Правило</th>
                        <th>Описание несоответствия</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(error_rows_html) if error_rows_html else '<tr><td colspan="5" class="center text-muted" style="padding: 24px;">Ошибок валидации не обнаружено. Все записи корректны!</td></tr>'}
                </tbody>
            </table>
        </div>

        <footer>
            Сгенерировано утилитой DataBridge 1.0.0 &bull; {now_str}
        </footer>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
