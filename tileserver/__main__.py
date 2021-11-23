import pathlib
from argparse import ArgumentParser

from tileserver.application import app

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-p", "--port", default=0, type=int)
    parser.add_argument("-d", "--debug", default=False, type=bool)
    args = parser.parse_args()

    filename = pathlib.Path(args.filename).expanduser().absolute()
    app.config["DEBUG"] = args.debug
    app.config["filename"] = filename
    app.run(host="localhost", port=args.port)
