"""Dataset statistical analysis and reporting for DataBridge."""

import os
from typing import Any, Dict, List, Optional
from ..readers.factory import get_reader


def infer_type(values: List[Any]) -> str:
    """Infer dominant data type of a list of non-empty values."""
    if not values:
        return "empty"

    int_count = 0
    float_count = 0
    bool_count = 0
    date_count = 0

    for val in values:
        s = str(val).strip()
        if s.lower() in ("true", "false", "yes", "no", "да", "нет"):
            bool_count += 1
            continue
        try:
            float_val = float(s.replace(",", "."))
            if float_val.is_integer() and "." not in s:
                int_count += 1
            else:
                float_count += 1
            continue
        except ValueError:
            pass

        if len(s) == 10 and (s[4] == "-" or s[2] == "." or s[2] == "/"):
            date_count += 1

    total = len(values)
    if int_count / total >= 0.8:
        return "integer"
    if (int_count + float_count) / total >= 0.8:
        return "float"
    if bool_count / total >= 0.8:
        return "boolean"
    if date_count / total >= 0.8:
        return "date"
    return "string"


class StatsReporter:
    """Analyzes data and generates summary statistics for console output."""

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        reader = get_reader(file_path)
        records = reader.read(file_path)

        file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        file_size_kb = file_size_bytes / 1024.0

        all_fields: List[str] = []
        for r in records:
            for k in r.keys():
                if not k.startswith("_") and k not in all_fields:
                    all_fields.append(k)

        column_stats: Dict[str, Dict[str, Any]] = {}
        for col in all_fields:
            col_vals = [r.get(col) for r in records]
            non_empty = [v for v in col_vals if v is not None and str(v).strip() != ""]
            empty_count = len(col_vals) - len(non_empty)
            unique_vals = set(str(v).strip() for v in non_empty)
            inferred = infer_type(non_empty)

            col_stat: Dict[str, Any] = {
                "total": len(col_vals),
                "non_empty": len(non_empty),
                "empty": empty_count,
                "unique": len(unique_vals),
                "inferred_type": inferred,
                "min": None,
                "max": None,
            }

            if inferred in ("integer", "float") and non_empty:
                try:
                    num_vals = [float(str(v).replace(",", ".")) for v in non_empty]
                    col_stat["min"] = min(num_vals)
                    col_stat["max"] = max(num_vals)
                except ValueError:
                    pass
            elif non_empty:
                col_stat["min"] = min(str(v) for v in non_empty)
                col_stat["max"] = max(str(v) for v in non_empty)

            column_stats[col] = col_stat

        return {
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "total_records": len(records),
            "columns": all_fields,
            "column_stats": column_stats,
        }

    @classmethod
    def print_stats(cls, file_path: str) -> None:
        stats = cls.analyze_file(file_path)

        print("=" * 65)
        print(f"СТАТИСТИКА ФАЙЛА: {stats['file_path']}")
        print("=" * 65)
        print(f"Размер файла:        {stats['file_size_kb']:.2f} КБ")
        print(f"Всего записей:       {stats['total_records']}")
        print(f"Количество колонок:  {len(stats['columns'])}")
        print("-" * 65)

        header = f"{'Колонка':<18} | {'Тип':<8} | {'Заполнено':<10} | {'Пустых':<8} | {'Уникальных':<10}"
        print(header)
        print("-" * 65)

        for col in stats["columns"]:
            cstat = stats["column_stats"][col]
            fill_rate = f"{cstat['non_empty']}/{stats['total_records']}"
            line = f"{col:<18} | {cstat['inferred_type']:<8} | {fill_rate:<10} | {cstat['empty']:<8} | {cstat['unique']:<10}"
            print(line)

        print("=" * 65)
