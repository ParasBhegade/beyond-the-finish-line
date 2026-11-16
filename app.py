import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from json import JSONDecodeError
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REQUIRED_FIELDS = {"Time", "Year", "Seconds", "Name", "Nationality", "Doping"}
LOGGER = logging.getLogger("tour-finish-times")


class ChartRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send_file(BASE_DIR / "index.html", "text/html; charset=utf-8")
        elif self.path == "/api/cyclist-data":
            self._send_cyclist_data()
        else:
            self.send_error(404)

    def _send_file(self, file_path, content_type):
        try:
            with file_path.open("rb") as file:
                body = file.read()
        except OSError:
            LOGGER.exception("Unable to read %s", file_path)
            self.send_error(500, "The chart page could not be loaded.")
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cyclist_data(self):
        try:
            with (BASE_DIR / "cyclist-data.json").open(encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, JSONDecodeError) as error:
            LOGGER.error("Unable to load cyclist data: %s", error)
            self._send_json(
                {"error": "Cyclist data could not be loaded."}, status=500
            )
            return

        if not isinstance(data, list) or any(
            not isinstance(row, dict) or not REQUIRED_FIELDS.issubset(row)
            for row in data
        ):
            LOGGER.error("Cyclist data source returned an unexpected format.")
            self._send_json(
                {"error": "Cyclist data has an unexpected format."}, status=502
            )
            return

        self._send_json(data)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ThreadingHTTPServer(("127.0.0.1", 5000), ChartRequestHandler).serve_forever()
