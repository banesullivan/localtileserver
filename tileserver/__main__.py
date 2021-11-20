from argparse import ArgumentParser
from .run import run_app


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--port", default=0, type=int)
    args = parser.parse_args()

    run_app(args.file, args.port)
