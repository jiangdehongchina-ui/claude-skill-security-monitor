#!/usr/bin/env python3
"""
Log Cleanup Tool - 日志清理工具
自动清理超过指定天数的旧日志文件
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

def cleanup_old_logs(log_dir, days=90, dry_run=False):
    """清理超过指定天数的日志文件"""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        print(f"[ERROR] Log directory not found: {log_dir}")
        return 0

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_count = 0
    deleted_size = 0

    print(f"Cleaning up logs older than {days} days...")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 查找所有归档的日志文件
    for log_file in log_dir.glob("security_events_*.jsonl"):
        try:
            # 从文件名提取时间戳
            timestamp_str = log_file.stem.replace("security_events_", "")
            file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)

            if file_date < cutoff_date:
                file_size = log_file.stat().st_size
                if dry_run:
                    print(f"  [DRY-RUN] Would delete: {log_file.name} ({file_size / 1024:.1f} KB)")
                else:
                    log_file.unlink()
                    print(f"  [DELETED] {log_file.name} ({file_size / 1024:.1f} KB)")
                deleted_count += 1
                deleted_size += file_size
        except (ValueError, OSError) as e:
            print(f"  [ERROR] Failed to process {log_file.name}: {e}")

    print()
    if dry_run:
        print(f"[DRY-RUN] Would delete {deleted_count} files ({deleted_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"[SUCCESS] Deleted {deleted_count} files ({deleted_size / 1024 / 1024:.2f} MB)")

    return deleted_count

def show_log_stats(log_dir):
    """显示日志统计信息"""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        print(f"[ERROR] Log directory not found: {log_dir}")
        return

    print("Log Statistics:")
    print("=" * 60)

    # 当前日志文件
    current_log = log_dir / "security_events.jsonl"
    if current_log.exists():
        size = current_log.stat().st_size
        print(f"Current log: {size / 1024:.1f} KB")
    else:
        print("Current log: [NOT FOUND]")

    # 归档日志文件
    archived_logs = list(log_dir.glob("security_events_*.jsonl"))
    if archived_logs:
        total_size = sum(f.stat().st_size for f in archived_logs)
        print(f"Archived logs: {len(archived_logs)} files, {total_size / 1024 / 1024:.2f} MB")

        # 显示最旧和最新的归档
        archived_logs.sort()
        print(f"  Oldest: {archived_logs[0].name}")
        print(f"  Newest: {archived_logs[-1].name}")
    else:
        print("Archived logs: None")

    # PostToolUse日志
    post_log = log_dir / "post_tool_events.jsonl"
    if post_log.exists():
        size = post_log.stat().st_size
        print(f"PostToolUse log: {size / 1024:.1f} KB")

    print("=" * 60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Log Cleanup Tool")
    parser.add_argument("--days", type=int, default=90, help="Delete logs older than N days (default: 90)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--stats", action="store_true", help="Show log statistics")

    args = parser.parse_args()

    log_dir = Path(__file__).parent.parent / "logs"

    if args.stats:
        show_log_stats(log_dir)
    else:
        cleanup_old_logs(log_dir, args.days, args.dry_run)

if __name__ == "__main__":
    main()
