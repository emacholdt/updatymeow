import sys
import argparse
from updatymeow.ecosystems import scan_all_ecosystems
from updatymeow.models import Status

def main(args: list[str] = None) -> int:
    parser = argparse.ArgumentParser(description="UpdatyMeow - Linux Software Updates in One Window")
    parser.add_argument("--check", action="store_true", help="Check for updates and print summary to terminal")
    parsed = parser.parse_args(args)

    if parsed.check:
        print("🔍 Checking for updates across Linux ecosystems...")
        items = scan_all_ecosystems()
        outdated = [i for i in items if i.status == Status.OUTDATED]
        print(f"Found {len(items)} items, {len(outdated)} update(s) available:")
        for item in outdated:
            major_tag = " [MAJOR]" if item.is_major else ""
            print(f"  • [{item.ecosystem.upper()}] {item.name}: {item.installed_version} -> {item.latest_version}{major_tag}")
        return 0

    # shortcut: fallback to GUI if not in CLI check mode
    from PyQt5.QtWidgets import QApplication
    from updatymeow.ui import MainWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.start_scan()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
