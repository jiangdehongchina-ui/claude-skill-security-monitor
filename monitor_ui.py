#!/usr/bin/env python3
"""
Skill Security Monitor — 实时监控终端 UI
基于 rich 库的彩色终端界面，实时显示安全事件
"""
import json
import time
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
except ImportError:
    print("Error: rich library required. Install with: pip install rich>=13.0")
    sys.exit(1)

DEFAULT_LOG = Path(__file__).parent / "logs" / "security_events.jsonl"
REFRESH_INTERVAL = 0.5  # seconds


class SecurityMonitor:
    """实时安全事件监控器"""

    def __init__(self, log_file, filter_tool=None, filter_decision=None,
                 show_stats=True):
        self.log_file = Path(log_file)
        self.filter_tool = filter_tool
        self.filter_decision = filter_decision
        self.show_stats = show_stats
        self.paused = False
        self.events = []
        self.max_display = 30
        self.last_size = 0
        self.console = Console()

    def load_events(self):
        """加载日志文件中的事件"""
        if not self.log_file.exists():
            return

        try:
            current_size = self.log_file.stat().st_size
            if current_size == self.last_size:
                return  # 无变化
            self.last_size = current_size
        except OSError:
            return

        new_events = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        new_events.append(event)
                    except json.JSONDecodeError:
                        continue
        except (OSError, IOError):
            return

        self.events = new_events

    def get_filtered_events(self):
        """获取过滤后的事件"""
        filtered = self.events
        if self.filter_tool:
            filtered = [e for e in filtered
                        if e.get("tool_name") == self.filter_tool]
        if self.filter_decision:
            filtered = [e for e in filtered
                        if e.get("decision") == self.filter_decision]
        return filtered[-self.max_display:]

    def build_stats_panel(self) -> Panel:
        """构建统计面板"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_events = [e for e in self.events
                        if e.get("timestamp", "").startswith(today)]

        total = len(today_events)
        denied = sum(1 for e in today_events if e.get("decision") == "deny")
        allowed = total - denied
        rate = (denied / total * 100) if total > 0 else 0

        last_time = ""
        if self.events:
            ts = self.events[-1].get("timestamp", "")
            if "T" in ts:
                last_time = ts.split("T")[1][:8]

        status = "[bold green]ACTIVE[/]" if not self.paused else "[bold yellow]PAUSED[/]"

        filters = []
        if self.filter_tool:
            filters.append(f"Tool={self.filter_tool}")
        if self.filter_decision:
            filters.append(f"Decision={self.filter_decision}")
        filter_text = f"  Filter: {', '.join(filters)}" if filters else ""

        stats_text = (
            f"  Status: {status}  |  "
            f"Events: [bold]{total}[/]  |  "
            f"Blocked: [bold red]{denied}[/]  |  "
            f"Allowed: [bold green]{allowed}[/]  |  "
            f"Block Rate: [bold]{rate:.1f}%[/]  |  "
            f"Last: {last_time}"
            f"{filter_text}"
        )

        return Panel(
            Text.from_markup(stats_text),
            title="[bold]Skill Security Monitor[/]",
            border_style="blue",
        )

    def build_event_table(self) -> Table:
        """构建事件表格"""
        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold cyan",
            expand=True,
        )
        table.add_column("Time", width=10, no_wrap=True)
        table.add_column("Tool", width=8, no_wrap=True)
        table.add_column("Decision", width=10, justify="center")
        table.add_column("Reason", ratio=2)
        table.add_column("ms", width=6, justify="right")

        for event in self.get_filtered_events():
            ts = event.get("timestamp", "")
            time_str = ts.split("T")[1][:8] if "T" in ts else ts[:8]

            tool = event.get("tool_name", "?")
            decision = event.get("decision", "?")
            reason = event.get("reason", "")
            exec_ms = event.get("execution_time_ms", 0)

            # 决策颜色
            if decision == "deny":
                dec_text = Text("DENY", style="bold red")
            else:
                dec_text = Text("ALLOW", style="bold green")

            # 严重级别颜色
            severity = event.get("severity", "")
            if severity in ("critical", "high"):
                reason_style = "red"
            elif severity == "medium":
                reason_style = "yellow"
            else:
                reason_style = ""

            table.add_row(
                time_str,
                tool,
                dec_text,
                Text(reason[:50], style=reason_style),
                f"{exec_ms:.1f}" if isinstance(exec_ms, (int, float)) else str(exec_ms),
            )

        return table

    def build_help_panel(self) -> Panel:
        """构建帮助面板"""
        help_text = (
            "[bold]q[/] Quit  "
            "[bold]f[/] Filter tool  "
            "[bold]d[/] Filter decision  "
            "[bold]c[/] Clear filters  "
            "[bold]s[/] Toggle stats  "
            "[bold]p[/] Pause/Resume  "
            "[bold]r[/] Refresh now"
        )
        return Panel(
            Text.from_markup(help_text),
            border_style="dim",
            height=3,
        )

    def build_display(self) -> Layout:
        """构建完整布局"""
        layout = Layout()

        if self.show_stats:
            layout.split_column(
                Layout(name="stats", size=3),
                Layout(name="events"),
                Layout(name="help", size=3),
            )
            layout["stats"].update(self.build_stats_panel())
        else:
            layout.split_column(
                Layout(name="events"),
                Layout(name="help", size=3),
            )

        layout["events"].update(self.build_event_table())
        layout["help"].update(self.build_help_panel())
        return layout

    def handle_key(self, key: str) -> bool:
        """处理键盘输入，返回 False 表示退出"""
        if key == "q":
            return False
        elif key == "p":
            self.paused = not self.paused
        elif key == "s":
            self.show_stats = not self.show_stats
        elif key == "c":
            self.filter_tool = None
            self.filter_decision = None
        elif key == "f":
            # 循环切换工具过滤
            tools = sorted(set(e.get("tool_name", "") for e in self.events))
            if not tools:
                return True
            if self.filter_tool is None:
                self.filter_tool = tools[0]
            else:
                idx = tools.index(self.filter_tool) if self.filter_tool in tools else -1
                if idx + 1 < len(tools):
                    self.filter_tool = tools[idx + 1]
                else:
                    self.filter_tool = None
        elif key == "d":
            # 切换决策过滤
            if self.filter_decision is None:
                self.filter_decision = "deny"
            elif self.filter_decision == "deny":
                self.filter_decision = "allow"
            else:
                self.filter_decision = None
        elif key == "r":
            self.last_size = 0  # 强制刷新
        return True

    def run(self):
        """主运行循环"""
        self.console.clear()
        self.console.print("[bold blue]Skill Security Monitor[/] starting...\n")

        if not self.log_file.exists():
            self.console.print(
                f"[yellow]Log file not found: {self.log_file}[/]\n"
                "Waiting for events..."
            )

        try:
            with Live(self.build_display(), console=self.console,
                       refresh_per_second=2, screen=True) as live:
                while True:
                    if not self.paused:
                        self.load_events()
                    live.update(self.build_display())

                    # 非阻塞键盘输入
                    key = self._get_key()
                    if key and not self.handle_key(key):
                        break

                    time.sleep(REFRESH_INTERVAL)
        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("\n[dim]Monitor stopped.[/]")

    def _get_key(self) -> str | None:
        """非阻塞读取单个按键"""
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                try:
                    return ch.decode("utf-8").lower()
                except UnicodeDecodeError:
                    return None
        else:
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).lower()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Skill Security Monitor - Real-time Terminal UI"
    )
    parser.add_argument(
        "--log-file", type=str, default=str(DEFAULT_LOG),
        help="Path to security events log file"
    )
    parser.add_argument(
        "--filter-tool", type=str, default=None,
        help="Filter by tool name (e.g., Bash, Write)"
    )
    parser.add_argument(
        "--filter-decision", type=str, default=None,
        choices=["allow", "deny"],
        help="Filter by decision"
    )
    parser.add_argument(
        "--no-stats", action="store_true",
        help="Hide statistics panel"
    )

    args = parser.parse_args()

    monitor = SecurityMonitor(
        log_file=args.log_file,
        filter_tool=args.filter_tool,
        filter_decision=args.filter_decision,
        show_stats=not args.no_stats,
    )
    monitor.run()


if __name__ == "__main__":
    main()
