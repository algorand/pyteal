setup-development:
	pip install -e.[development]

setup-docs: setup-development
	pip install -r docs/requirements.txt
	pip install doc2dash

setup-wheel:
	pip install wheel

bdist-wheel:
	python setup.py sdist bdist_wheel

bundle-docs-clean:
	rm -rf docs/pyteal.docset

bundle-docs: bundle-docs-clean
	cd docs && \
	make html && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

generate-init:
	python -m scripts.generate_init

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples pyteal scripts tests *.py
black:
	black --check $(ALLPY)

flake8:
	flake8 $(ALLPY)

MYPY = pyteal scripts
mypy:
	mypy $(MYPY)

lint: black flake8 mypy

test-unit:
	pytest

build-and-test: check-generate-init lint test-unit

# Extras:
coverage:
	pytest --cov-report html --cov=pyteal
