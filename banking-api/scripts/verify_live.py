"""Start a real Uvicorn server, exercise HTTP CRUD, and stop our process."""

from pathlib import Path
import re
import socket
import subprocess
import sys
import time

import httpx


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 8000))
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("Uvicorn exited before startup")
                try:
                    response = client.get("/")
                    break
                except httpx.ConnectError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Server did not start within 10 seconds")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            docs = client.get("/docs")
            assert docs.status_code == 200 and "SwaggerUIBundle" in docs.text
            assets = re.findall(r'(?:src|href)="(https://[^\"]+\.(?:js|css))"', docs.text)
            assert len(assets) >= 2
            for url in assets:
                assert client.get(url).status_code == 200, url
            schema = client.get("/openapi.json")
            assert schema.status_code == 200
            assert "/accounts/{id}" in schema.json()["paths"]
            assert len(client.get("/accounts").json()) == 3
            assert client.get("/accounts/1").json()["balance"] == "1250.50"
            payload = {"account_holder": "Taylor Brown", "account_type": "savings", "balance": "500.00"}
            created = client.post("/accounts", json=payload)
            assert created.status_code == 201
            path = created.headers["location"]
            assert client.get(path).json() == {"id": 4, **payload}
            payload["balance"] = "750.25"
            assert client.put(path, json=payload).status_code == 200
            assert client.get(path).json()["balance"] == "750.25"
            invalid = client.post("/accounts", json={**payload, "balance": "-1"})
            assert invalid.status_code == 422
            deleted = client.delete(path)
            assert deleted.status_code == 204 and deleted.content == b""
            assert client.get(path).status_code == 404
            assert client.put(path, json=payload).status_code == 404
            assert client.delete(path).status_code == 404
            assert len(client.get("/accounts").json()) == 3
            print("PASS: real server startup, Swagger HTML/assets, OpenAPI, sample data, CRUD, validation, and 404s")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
