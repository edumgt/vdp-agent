import os

from api_server import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", "8081"))
    app.run(host="0.0.0.0", port=port)
