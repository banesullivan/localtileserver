from argparse import ArgumentParser
from .server import run_app


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("--debug", default=False, type=bool)
    args = parser.parse_args()

    run_app(args.file, args.port, args.debug)
