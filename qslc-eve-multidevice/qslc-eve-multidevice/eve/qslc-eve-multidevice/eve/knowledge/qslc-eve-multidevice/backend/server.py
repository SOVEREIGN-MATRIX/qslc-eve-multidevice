import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import glob

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT_PATH = os.getenv("EVE_SYSTEM_PROMPT_PATH", "./eve/eve_prompt.txt")
KNOWLEDGE_DIR = os.getenv("EVE_KNOWLEDGE_DIR", "./eve/knowledge")


def load_system_prompt():
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are EVE-HEI, but your system prompt file is missing."


def load_knowledge():
    chunks = []
    for path in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                chunks.append(f.read())
        except Exception:
            continue
    return "\n\n".join(chunks)


class EVEHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/chat":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode("utf-8"))
            return

        user_message = data.get("message", "")
        if not user_message:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Missing 'message'"}).encode("utf-8"))
            return

        system_prompt = load_system_prompt()
        knowledge = load_knowledge()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Knowledge base:\n{knowledge}"},
            {"role": "user", "content": user_message},
        ]

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
        }

        try:
            resp = requests.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"EVE-HEI backend error: {e}"

        self._set_headers(200)
        self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=EVEHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"EVE-HEI backend running on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
