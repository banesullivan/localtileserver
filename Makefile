# Simple makefile to simplify repetitive build env management tasks under posix

CODESPELL_DIRS ?= ./
CODESPELL_SKIP ?= "*.pyc,*.txt,*.gif,*.png,*.jpg,*.ply,*.vtk,*.vti,*.js,*.html,*.doctree,*.ttf,*.woff,*.woff2,*.eot,*.mp4,*.inv,*.pickle,*.ipynb,flycheck*,./.git/*,./.hypothesis/*,*.yml,./doc/_build/*,./doc/images/*,./dist/*,*~,.hypothesis*,./doc/examples/*,*.mypy_cache/*,*cover,./tests/tinypages/_build/*,*/_autosummary/*"
CODESPELL_IGNORE ?= "ignore_words.txt"


stylecheck: codespell lint

codespell:
	@echo "Running codespell"
	@codespell $(CODESPELL_DIRS) -S $(CODESPELL_SKIP) -I $(CODESPELL_IGNORE)

pydocstyle:
	@echo "Running pydocstyle"
	@pydocstyle localtileserver --match='(?!coverage).*.py'

doctest:
	@echo "Runnnig module doctesting"
	pytest -v --doctest-modules localtileserver

lint:
	@echo "Linting with flake8"
	flake8 --ignore=E501 localtileserver tests

format:
	@echo "Formatting"
	black .
	isort .
