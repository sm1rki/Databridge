"""Console summary reporting for DataBridge."""

from typing import List, Optional
from ..validators.models import ValidationError
from ..converters.pipeline import PipelineResult


def format_console_summary(
    total: int,
    valid: int,
    errors: int,
    error_list: List[ValidationError],
    output_file: Optional[str] = None,
    errors_file: Optional[str] = None,
    report_file: Optional[str] = None,
    max_displayed_errors: int = 15,
) -> str:
    """Format user-friendly console summary matching the ТЗ specification."""
    lines: List[str] = [
        f"Всего записей: {total}",
        f"Успешно обработано: {valid}",
        f"Ошибок: {errors}",
    ]

    if error_list:
        for err in error_list[:max_displayed_errors]:
            lines.append(f"  - Строка {err.row_number}: поле \"{err.field}\" {err.message}")

        if len(error_list) > max_displayed_errors:
            lines.append(f"  ... и ещё {len(error_list) - max_displayed_errors} ошибок")

    if output_file:
        lines.append(f"Результат сохранён: {output_file}")
    if errors_file and errors > 0:
        lines.append(f"Ошибки сохранены: {errors_file}")
    if report_file:
        lines.append(f"Отчёт сохранён: {report_file}")

    return "\n".join(lines)


def print_pipeline_summary(res: PipelineResult, max_displayed_errors: int = 15) -> None:
    """Print pipeline execution summary directly to console."""
    error_list: List[ValidationError] = []
    if res.validation_result:
        error_list = res.validation_result.errors

    text = format_console_summary(
        total=res.total_records,
        valid=res.valid_records,
        errors=res.error_records,
        error_list=error_list,
        output_file=res.output_file,
        errors_file=res.errors_file,
        report_file=res.report_file,
        max_displayed_errors=max_displayed_errors,
    )
    print(text)
