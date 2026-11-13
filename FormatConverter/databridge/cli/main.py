"""Command Line Interface for DataBridge."""

import argparse
import sys
import os
from typing import List, Optional

from ..readers.base import ReaderError
from ..writers.base import WriterError
from ..validators.engine import ValidationEngine, ConfigError
from ..converters.pipeline import ConversionPipeline
from ..converters.mapper import FieldMapper
from ..reporters.console import format_console_summary
from ..reporters.html_reporter import HTMLReporter
from ..reporters.stats_reporter import StatsReporter


def create_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="databridge",
        description="DataBridge — утилита для чтения, валидации и конвертации табличных данных (CSV, JSON, XML, Excel).",
        epilog="Пример: databridge convert data.csv --to json --config schema.yaml --output result.json"
    )
    subparsers = parser.add_subparsers(dest="command", title="Команды", help="Доступные команды")

    # Command: convert
    convert_parser = subparsers.add_parser("convert", help="Конвертировать данные в другой формат с валидацией")
    convert_parser.add_argument("input", help="Путь к исходному файлу данных (.csv, .json, .xml, .xlsx)")
    convert_parser.add_argument("--to", dest="to_format", choices=["json", "csv", "xml", "excel", "xlsx"], help="Целевой формат конвертации")
    convert_parser.add_argument("--output", "-o", dest="output", help="Путь для сохранения файла результата")
    convert_parser.add_argument("--config", "-c", dest="config", help="Путь к файлу конфигурации правил (schema.yaml или schema.json)")
    convert_parser.add_argument("--errors", "-e", dest="errors", default="errors.csv", help="Путь для сохранения строк с ошибками (по умолчанию: errors.csv)")
    convert_parser.add_argument("--report", "-r", dest="report", help="Путь для сохранения HTML-отчёта (например: report.html)")
    convert_parser.add_argument("--delimiter", dest="delimiter", default=None, help="Разделитель для CSV (по умолчанию: автоопределение или запятая)")
    convert_parser.add_argument("--sheet", dest="sheet", default=None, help="Имя листа для Excel файлов")

    # Command: validate
    validate_parser = subparsers.add_parser("validate", help="Проверить данные на соответствие правилам схемы")
    validate_parser.add_argument("input", help="Путь к файлу данных для валидации")
    validate_parser.add_argument("--config", "-c", dest="config", required=True, help="Путь к файлу конфигурации правил (schema.yaml или schema.json)")
    validate_parser.add_argument("--report", "-r", dest="report", help="Путь для генерации HTML-отчёта (например: report.html)")
    validate_parser.add_argument("--errors", "-e", dest="errors", default="errors.csv", help="Путь для сохранения строк с ошибками (по умолчанию: errors.csv)")
    validate_parser.add_argument("--delimiter", dest="delimiter", default=None, help="Разделитель для CSV файлов")

    # Command: stats
    stats_parser = subparsers.add_parser("stats", help="Вывести статистику и структуру файла")
    stats_parser.add_argument("input", help="Путь к анализируемому файлу")

    return parser


def handle_convert(args: argparse.Namespace) -> int:
    """Handle convert command."""
    validator_engine: Optional[ValidationEngine] = None
    field_mapper: Optional[FieldMapper] = None

    if args.config:
        validator_engine = ValidationEngine.load_config(args.config)
        field_mapper = FieldMapper(config=validator_engine.config)

    # Determine output file and format
    out_file = args.output
    to_fmt = args.to_format

    if not out_file and not to_fmt:
        print("Ошибка: необходимо указать либо целевой файл (--output), либо целевой формат (--to).", file=sys.stderr)
        return 1

    if not out_file and to_fmt:
        base, _ = os.path.splitext(args.input)
        ext = ".xlsx" if to_fmt in ("excel", "xlsx") else f".{to_fmt}"
        out_file = f"{base}_converted{ext}"

    pipeline = ConversionPipeline(
        validator_engine=validator_engine,
        field_mapper=field_mapper,
        skip_invalid=True,
    )

    input_opts = {}
    if args.delimiter:
        input_opts["delimiter"] = args.delimiter
    if args.sheet:
        input_opts["sheet_name"] = args.sheet

    res = pipeline.run(
        input_file=args.input,
        output_file=out_file,
        to_format=to_fmt,
        errors_file=args.errors if (validator_engine and res_has_errors(validator_engine, args)) else args.errors,
        input_options=input_opts,
    )

    # Generate HTML report if requested
    if args.report and res.validation_result:
        reporter = HTMLReporter()
        reporter.generate(
            output_path=args.report,
            input_file=args.input,
            output_file=out_file,
            errors_file=args.errors if res.error_records > 0 else None,
            config_file=args.config,
            validation_result=res.validation_result,
        )
        res.report_file = args.report

    # Print summary
    errors_list = res.validation_result.errors if res.validation_result else []
    summary = format_console_summary(
        total=res.total_records,
        valid=res.valid_records,
        errors=res.error_records,
        error_list=errors_list,
        output_file=res.output_file,
        errors_file=res.errors_file if res.error_records > 0 else None,
        report_file=res.report_file,
    )
    print(summary)

    return 0


def res_has_errors(validator_engine: ValidationEngine, args: argparse.Namespace) -> bool:
    return True


def handle_validate(args: argparse.Namespace) -> int:
    """Handle validate command."""
    validator_engine = ValidationEngine.load_config(args.config)
    pipeline = ConversionPipeline(validator_engine=validator_engine, skip_invalid=False)

    input_opts = {}
    if args.delimiter:
        input_opts["delimiter"] = args.delimiter

    res = pipeline.run(
        input_file=args.input,
        output_file=None,
        errors_file=args.errors,
        input_options=input_opts,
    )

    if args.report and res.validation_result:
        reporter = HTMLReporter()
        reporter.generate(
            output_path=args.report,
            input_file=args.input,
            output_file=None,
            errors_file=args.errors if res.error_records > 0 else None,
            config_file=args.config,
            validation_result=res.validation_result,
        )
        res.report_file = args.report

    errors_list = res.validation_result.errors if res.validation_result else []
    summary = format_console_summary(
        total=res.total_records,
        valid=res.valid_records,
        errors=res.error_records,
        error_list=errors_list,
        output_file=None,
        errors_file=res.errors_file if res.error_records > 0 else None,
        report_file=res.report_file,
    )
    print(summary)

    return 0 if res.error_records == 0 else 1


def handle_stats(args: argparse.Namespace) -> int:
    """Handle stats command."""
    StatsReporter.print_stats(args.input)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = create_parser()

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)

        if args.command == "convert":
            return handle_convert(args)
        elif args.command == "validate":
            return handle_validate(args)
        elif args.command == "stats":
            return handle_stats(args)
        else:
            parser.print_help()
            return 0

    except (ReaderError, WriterError, ConfigError) as e:
        print(f"Ошибка: {str(e)}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Файл не найден: {e.filename or str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
