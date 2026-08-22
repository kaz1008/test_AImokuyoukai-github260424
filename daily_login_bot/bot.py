"""日次ログイン/スクラッチ自動化スクリプト。

前提: 自分が所有する端末・アカウントに対してのみ実行すること。
対象アプリが自動操作を規約で禁止していないか、事前に必ず確認すること。

使い方:
    python bot.py            # config.yaml の手順を1回実行
    python bot.py --dry-run  # 端末に接続し、スクリーンショットのみ撮って手順は実行しない
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

import uiautomator2 as u2
import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def connect_device(serial: str | None):
    d = u2.connect(serial) if serial else u2.connect()
    if not d.info:
        raise RuntimeError("端末に接続できませんでした。`adb devices` で接続状態を確認してください。")
    return d


def wake_and_unlock(d) -> None:
    if not d.info.get("screenOn", False):
        d.screen_on()
    d.unlock()


def run_steps(d, steps: list[dict]) -> None:
    for i, step in enumerate(steps, start=1):
        action = step.get("action")
        if action == "tap":
            if "text" in step:
                target = d(text=step["text"])
            elif "resource_id" in step:
                target = d(resourceId=step["resource_id"])
            else:
                raise ValueError(f"手順{i}: text か resource_id を指定してください: {step}")
            if not target.wait(timeout=10):
                raise RuntimeError(f"手順{i}: 対象要素が見つかりませんでした: {step}")
            target.click()
        elif action == "wait":
            d.sleep(step.get("seconds", 1))
        else:
            raise ValueError(f"手順{i}: 未対応のactionです: {action}")


def save_screenshot(d, screenshot_dir: Path, label: str) -> Path:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = screenshot_dir / f"{timestamp}_{label}.png"
    d.screenshot(str(path))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="手順を実行せずスクリーンショットのみ撮る")
    args = parser.parse_args()

    config = load_config()
    device_cfg = config.get("device", {})
    app_cfg = config["app"]
    log_cfg = config.get("logging", {})
    screenshot_dir = Path(log_cfg.get("screenshot_dir", "./logs"))

    d = connect_device(device_cfg.get("serial") or None)
    wake_and_unlock(d)

    d.app_start(app_cfg["package_name"], stop=True)
    d.sleep(app_cfg.get("launch_wait_seconds", 5))

    if args.dry_run:
        path = save_screenshot(d, screenshot_dir, "dry_run")
        print(f"dry-run: スクリーンショットを保存しました -> {path}")
        return 0

    try:
        run_steps(d, app_cfg.get("steps", []))
    except Exception as e:
        path = save_screenshot(d, screenshot_dir, "error")
        print(f"エラーが発生しました: {e}\nスクリーンショット -> {path}", file=sys.stderr)
        return 1

    path = save_screenshot(d, screenshot_dir, "success")
    print(f"完了しました。スクリーンショット -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
