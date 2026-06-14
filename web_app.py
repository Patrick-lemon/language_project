from __future__ import annotations

import json
import mimetypes
import os
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from runtime_support import configure_text_output, load_dotenv
from voice_tutor import VoiceTutorSessionManager


HOST = "127.0.0.1"
PORT = int(os.environ.get("TUTOR_WEB_PORT", "8765"))
WEB_DIR = Path(__file__).resolve().parent / "web"
SESSION_MANAGER = VoiceTutorSessionManager()


class TutorWebHandler(BaseHTTPRequestHandler):
    server_version = "LanguageTutorWeb/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._serve_file(WEB_DIR / "index.html")
            return
        if path == "/app.js":
            self._serve_file(WEB_DIR / "app.js")
            return
        if path == "/styles.css":
            self._serve_file(WEB_DIR / "styles.css")
            return
        if path == "/static/app.js":
            self._serve_file(WEB_DIR / "app.js")
            return
        if path == "/static/styles.css":
            self._serve_file(WEB_DIR / "styles.css")
            return
        if path == "/api/config":
            self._send_json(SESSION_MANAGER.config_payload())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/session/start":
                response = SESSION_MANAGER.start_session(
                    learner_name=str(payload.get("learner_name") or "Student").strip()
                    or "Student",
                    focus_mode=str(payload.get("focus_mode") or "balanced"),
                    custom_topics=payload.get("custom_topics"),
                )
                self._send_json(response)
                return
            if path == "/api/session/respond":
                response = SESSION_MANAGER.respond(
                    str(payload.get("session_id") or ""),
                    str(payload.get("learner_text") or ""),
                    [
                        str(item)
                        for item in payload.get("alternatives", [])
                        if str(item).strip()
                    ]
                    if isinstance(payload.get("alternatives"), list)
                    else None,
                )
                self._send_json(response)
                return
            if path == "/api/session/advance":
                response = SESSION_MANAGER.advance(str(payload.get("session_id") or ""))
                self._send_json(response)
                return
            if path == "/api/session/next":
                response = SESSION_MANAGER.next_lesson(str(payload.get("session_id") or ""))
                self._send_json(response)
                return
            if path == "/api/session/focus":
                response = SESSION_MANAGER.update_focus(
                    str(payload.get("session_id") or ""),
                    focus_mode=str(payload.get("focus_mode") or "balanced"),
                    custom_topics=payload.get("custom_topics"),
                )
                self._send_json(response)
                return
        except KeyError:
            self._send_json({"error": "Unknown session id."}, status=HTTPStatus.NOT_FOUND)
            return
        except json.JSONDecodeError:
            self._send_json(
                {"error": "Request body must be valid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("JSON body must be an object", raw, 0)
        return parsed

    def _send_json(
        self,
        payload: dict[str, object],
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type = f"{content_type}; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server() -> None:
    load_dotenv()
    configure_text_output()
    address = f"http://{HOST}:{PORT}"
    print(f"Voice tutor web app running at {address}")
    print("Open that URL in Chrome or Edge for microphone support.")
    try:
        server = ThreadingHTTPServer((HOST, PORT), TutorWebHandler)
    except OSError as exc:
        print(
            f"Could not start the web app on {address}. "
            f"The port may already be in use. ({exc})"
        )
        print("Close the old server or run again with TUTOR_WEB_PORT set to a different port.")
        return

    if os.environ.get("TUTOR_NO_BROWSER", "").strip().lower() not in {"1", "true", "yes"}:
        threading.Timer(0.8, lambda: webbrowser.open(address)).start()
    with server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping web app.")


if __name__ == "__main__":
    run_server()
