import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import engine


class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_POST(self):
        if self.path != "/evaluate":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid json"}).encode("utf-8"))
            return

        inputs = payload.get("inputs")
        sequence = payload.get("operator_sequence")
        case_id = payload.get("case_id", "api_case")

        if not isinstance(inputs, dict) or not isinstance(sequence, list) or not sequence:
            self._set_headers(400)
            self.wfile.write(
                json.dumps({"error": "inputs must be object and operator_sequence must be non-empty list"}).encode("utf-8")
            )
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        operators_dir = os.path.join(base_dir, "operators")

        try:
            result = engine.run_inputs(case_id, inputs, sequence, operators_dir)
        except Exception as exc:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
            return

        self._set_headers(200)
        self.wfile.write(json.dumps(result).encode("utf-8"))


def main():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
