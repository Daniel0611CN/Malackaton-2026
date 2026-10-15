"""
Genera el informe HTML a partir de los resultados JSON de los tests.

Uso:
    python scripts/build_report.py reports/betsson_com          # informe de un mercado
    python scripts/build_report.py reports --summary            # índice combinado + resumen Markdown
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.report_helper import build_html_report, build_markdown_summary  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir")
    parser.add_argument("--title", default="Betsson · Intelligent Game Validation")
    parser.add_argument("--summary", action="store_true", help="Escribe la tabla en $GITHUB_STEP_SUMMARY")
    args = parser.parse_args()

    path = build_html_report(args.results_dir, title=args.title)
    print(f"Informe generado: {path}")

    if args.summary:
        md = f"## {args.title}\n\n{build_markdown_summary(args.results_dir)}\n"
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(md)
        else:
            print(md)


if __name__ == "__main__":
    main()
