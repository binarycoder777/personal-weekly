import sys
import argparse
from datetime import datetime
from pathlib import Path
import re

def check_weekly_generation(expect_current_month: bool = False):
    """检查周刊是否正常生成"""
    today = datetime.now()
    year = today.year
    month = today.month

    root_dir = Path(__file__).resolve().parents[1]
    content_dir = root_dir / "src" / "content" / "docs"
    current_month_dir = content_dir / f"{year}年" / f"{month}月"

    if expect_current_month:
        if not current_month_dir.is_dir():
            print(f"错误: 目录不存在 {current_month_dir}")
            return False
        mdx_files = list(current_month_dir.glob("*.mdx"))
        checked_path = current_month_dir
    else:
        mdx_files = list(content_dir.rglob("*.mdx"))
        checked_path = content_dir

    if not mdx_files:
        print(f"错误: 未找到 MDX 文件在 {checked_path}")
        return False

    def publication_key(path: Path) -> tuple[int, int, int]:
        match = re.search(r"(\d{4})年/(\d{1,2})月/(\d{1,2})期\.mdx$", path.as_posix())
        return tuple(map(int, match.groups())) if match else (0, 0, 0)

    newest_issue = max(mdx_files, key=publication_key)
    print(f"健康检查通过：发现 {len(mdx_files)} 篇内容，最新文件为 {newest_issue.relative_to(content_dir)}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检查周刊内容是否正常生成")
    parser.add_argument(
        "--expect-current-month",
        action="store_true",
        help="要求当前年月目录中至少生成一篇 MDX；供生成工作流使用。",
    )
    args = parser.parse_args()
    success = check_weekly_generation(args.expect_current_month)
    sys.exit(0 if success else 1)
