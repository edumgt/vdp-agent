import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .routes import register_routes


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    local_pdf_dir = os.path.abspath(os.environ.get("LOCAL_PDF_DIR", "./storage/pdfs"))

    @app.get("/files/<path:filename>")
    def files(filename):
        return send_from_directory(local_pdf_dir, filename)

    register_routes(app)
    return app
