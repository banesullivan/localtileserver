from argparse import ArgumentParser
import pathlib

from tileserver.application import app
from tileserver.application.paths import inject_path


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("--debug", default=False, type=bool)
    args = parser.parse_args()

    path = pathlib.Path(args.file).expanduser()
    inject_path("default", path)
    app.config["DEBUG"] = args.debug
    app.run(host="localhost", port=args.port)
