import logging
import sys

from flask import Flask

app = Flask(__name__)


@app.route('/')
def home():
    with open("index.html", "r") as f:
        data = f.read()
    return data


@app.route("/index.js")
def react():
    return "const root = ReactDOM.createRoot(document.getElementById('root'));\n" \
           "root.render(<h1>Hello, world!</h1>);"


def main():
    log = logging.getLogger('werkzeug')
    log.disabled = True
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    app.run("127.0.0.1", 5000)


if __name__ == '__main__':
    main()
