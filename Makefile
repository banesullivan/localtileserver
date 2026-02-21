# Simple makefile to simplify repetitive build env management tasks under posix

DOCKER_IMAGE     ?= localtileserver
DOCKER_IMAGE_JUP ?= $(DOCKER_IMAGE)-jupyter
PORT             ?= 8000

.PHONY: install lint format test doctest coverage docs docs-serve \
        docker-build docker-build-jupyter docker-run \
        build clean clean-test-images report

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	pre-commit run --all-files

format:
	ruff format localtileserver tests
	ruff check --fix localtileserver tests

test:
	pytest --cov=localtileserver

doctest:
	@echo "Running module doctesting"
	pytest -v --doctest-modules localtileserver

coverage:
	pytest --cov=localtileserver --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

docs:
	LOCALTILESERVER_BUILDING_DOCS=true $(MAKE) -C doc html

docs-serve:
	$(MAKE) -C doc serve-html

build-slim:
	docker build -t $(DOCKER_IMAGE) --target slim .

build-jupyter:
	docker build -t $(DOCKER_IMAGE_JUP) --target jupyter .

build: build-slim build-jupyter

docker-run:
	docker run --rm -it -p $(PORT):8000 $(DOCKER_IMAGE)

jupyter:
	docker run --rm -it -p 8888:8888 $(DOCKER_IMAGE_JUP)

serve:
	uvicorn localtileserver.web.wsgi:app --host 0.0.0.0 --port $(PORT) --reload

report:
	python -c "import localtileserver; print(localtileserver.Report())"

clean-test-images:
	@echo "Cleaning test images"
	rm -rf tests/baseline/
	rm -rf tests/generated/

clean: clean-test-images
	rm -rf dist/ build/ *.egg-info
	rm -rf doc/build
	rm -rf htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
