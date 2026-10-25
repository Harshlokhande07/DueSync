import os
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def app(environ, start_response):
    """
    Standard WSGI entrypoint for Vercel Python runtime.
    Serves DueSync static web application and assets with zero dependencies.
    """
    path = environ.get("PATH_INFO", "/").lstrip("/")
    if not path:
        target = os.path.join(BASE_DIR, "index.html")
    else:
        target = os.path.join(BASE_DIR, path)

    if not os.path.isfile(target):
        target = os.path.join(BASE_DIR, "index.html")

    mime, _ = mimetypes.guess_type(target)
    content_type = mime or "text/html; charset=utf-8"

    try:
        with open(target, "rb") as f:
            body = f.read()
        status = "200 OK"
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body)))
        ]
        start_response(status, headers)
        return [body]
    except Exception as e:
        status = "500 Internal Server Error"
        headers = [("Content-Type", "text/plain; charset=utf-8")]
        start_response(status, headers)
        return [str(e).encode("utf-8")]

# Also expose handler for AWS Lambda / Vercel Serverless style invocations
handler = app
