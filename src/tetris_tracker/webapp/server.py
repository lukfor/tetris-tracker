import argparse
import html
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from tetris_tracker.webapp import dashboard
from tetris_tracker.webapp import run_detail


def render_path(path, db):
    if path in ("/", "/index.html"):
        return dashboard.render(db)

    if path.startswith("/run/"):
        try:
            run_id = int(path.rsplit("/", 1)[-1])
        except ValueError:
            return None

        return run_detail.render(db, run_id)

    return None


def serve(db, host, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path

            try:
                body = render_path(path, db)

                if body is None:
                    self.send_error(404)
                    return

                body = body.encode("utf-8")
                self.send_response(200)

            except sqlite3.Error as exc:
                body = (
                    "<h1>Database error</h1>"
                    "<pre>{}</pre>"
                ).format(
                    html.escape(str(exc))
                ).encode("utf-8")

                self.send_response(500)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )
            self.send_header(
                "Cache-Control",
                "no-store",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(
        (host, port),
        Handler,
    )

    print(
        "Tetris Tracker web: "
        "http://{}:{} "
        "db={}".format(host, port, db),
        flush=True,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(
        prog="tetris-tracker-web"
    )

    parser.add_argument(
        "--db",
        default="./tetris.db",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8001,
    )

    args = parser.parse_args()

    serve(
        args.db,
        args.host,
        args.port,
    )


if __name__ == "__main__":
    main()
