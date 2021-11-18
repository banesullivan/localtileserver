if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()

    from .application import app

    app.config["path"] = args.file
    app.run(host="127.0.0.1", port=args.port)
