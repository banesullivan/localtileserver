if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--port", default=5001, type=int)
    args = parser.parse_args()

    from .application import app

    app.config["path"] = args.file
    app.run(host="localhost", port=args.port)
