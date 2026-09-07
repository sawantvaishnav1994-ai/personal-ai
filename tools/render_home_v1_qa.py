from __future__ import annotations

import argparse
import base64
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


class DummyEvents:
    def subscribe(self, *_args, **_kwargs):
        return lambda: None


class DummyExecutor:
    def chat(self, text):
        return f"Rendered response to: {text}"

    def approve(self, _approval_id):
        return "Approved"

    def reject(self, _approval_id):
        return "Rejected"


class DummyMemory:
    def graph(self):
        nodes = [{"id": f"n{i}"} for i in range(12)]
        edges = [{"id": f"e{i}"} for i in range(19)]
        return {"nodes": nodes, "edges": edges}


STATES = ("idle", "listening", "thinking", "memory", "speaking")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="visual-qa")
    parser.add_argument("--emit-idle-base64", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    window = MainWindow(
        events=DummyEvents(),
        executor=DummyExecutor(),
        memory=DummyMemory(),
        runtime={},
    )
    window.resize(1200, 760)
    window.show()
    app.processEvents()

    for state in STATES:
        window._set_state(state)
        app.processEvents()
        path = out / f"home-v1-{state}.png"
        window.grab().save(str(path), "PNG")
        print(f"rendered:{state}:{path}")

    if args.emit_idle_base64:
        data = (out / "home-v1-idle.png").read_bytes()
        print("IDLE_PNG_BASE64_BEGIN")
        print(base64.b64encode(data).decode("ascii"))
        print("IDLE_PNG_BASE64_END")

    window.close()
    app.quit()


if __name__ == "__main__":
    main()
