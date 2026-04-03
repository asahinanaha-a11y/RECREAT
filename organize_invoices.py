#!/usr/bin/env python3
"""
請求書ファイルを月別フォルダに自動振り分けするスクリプト

使い方:
    python organize_invoices.py <請求書が入っているフォルダのパス>

ファイル名に含まれるキーワードで振り分け:
  - 「支払」を含む → 支払い請求書/YYYY/MM月/
  - それ以外       → 請求書/YYYY/MM月/

日付の判定:
  1. ファイル名に YYYY-MM, YYYY_MM, YYYYMM のパターンがあればその年月を使用
  2. なければファイルの最終更新日を使用
"""

import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ファイル名から年月を抽出するパターン
DATE_PATTERNS = [
    re.compile(r"(\d{4})[-_/年](\d{1,2})[-_/月]"),  # 2026-04, 2026_04, 2026年04月
    re.compile(r"(\d{4})(\d{2})"),                     # 202604
]

PAYMENT_KEYWORDS = ["支払", "支払い", "shiharai"]

INVOICE_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".csv", ".docx", ".doc",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
}


def extract_date_from_filename(filename: str) -> tuple[int, int] | None:
    """ファイル名から年月を抽出する。見つからなければNoneを返す。"""
    for pattern in DATE_PATTERNS:
        match = pattern.search(filename)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            if 2000 <= year <= 2099 and 1 <= month <= 12:
                return year, month
    return None


def get_file_date(filepath: Path) -> tuple[int, int]:
    """ファイルの最終更新日から年月を取得する。"""
    mtime = os.path.getmtime(filepath)
    dt = datetime.fromtimestamp(mtime)
    return dt.year, dt.month


def is_payment_invoice(filename: str) -> bool:
    """支払い請求書かどうかを判定する。"""
    return any(kw in filename for kw in PAYMENT_KEYWORDS)


def organize(source_dir: str) -> None:
    source = Path(source_dir).resolve()
    if not source.is_dir():
        print(f"エラー: '{source_dir}' はフォルダではありません。")
        sys.exit(1)

    moved = 0
    skipped = 0

    for filepath in sorted(source.iterdir()):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in INVOICE_EXTENSIONS:
            continue

        filename = filepath.name

        # 年月を判定
        date_info = extract_date_from_filename(filename)
        if date_info:
            year, month = date_info
        else:
            year, month = get_file_date(filepath)

        # 振り分け先を決定
        if is_payment_invoice(filename):
            category = "支払い請求書"
        else:
            category = "請求書"

        dest_dir = BASE_DIR / category / str(year) / f"{month:02d}月"
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / filename
        if dest_path.exists():
            print(f"  スキップ (既存): {filename}")
            skipped += 1
            continue

        shutil.copy2(filepath, dest_path)
        print(f"  {category}/{year}/{month:02d}月/{filename}")
        moved += 1

    print(f"\n完了: {moved} 件移動, {skipped} 件スキップ")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python organize_invoices.py <請求書フォルダのパス>")
        print("例:     python organize_invoices.py ~/Desktop/請求書")
        sys.exit(1)

    print(f"請求書を整理中: {sys.argv[1]}\n")
    organize(sys.argv[1])
