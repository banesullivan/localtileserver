# Simple makefile to simplify repetitive build env management tasks under posix

lint:
	pre-commit run --all-files

doctest:
	@echo "Running module doctesting"
	pytest -v --doctest-modules localtileserver

clean-test-images:
	@echo "Cleaning test images"
	rm -rf tests/baseline/
	rm -rf tests/generated/
