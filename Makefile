# ---- Setup ---- #

setup-development:
	pip install -e .
	pip install -r requirements.txt --upgrade

setup-docs:
	pip install -r docs/requirements.txt
	pip install doc2dash

setup-wheel:
	pip install wheel

generate-init:
	python -m scripts.generate_init

# ---- Docs and Distribution ---- #

bdist-wheel:
	python setup.py sdist bdist_wheel

bundle-docs-clean:
	rm -rf docs/pyteal.docset
	rm -rf docs/_build
	rm -f docs/pyteal.docset.tar.gz

bundle-docs: bundle-docs-clean
	cd docs && \
	make html SPHINXOPTS="-W --keep-going" && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

# ---- Code Quality ---- #

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples feature_gates pyteal scripts tests *.py
black:
	black --check $(ALLPY)

flake8:
	flake8 $(ALLPY)

mypy:
	mypy

sdist-check:
	python setup.py check -s
	python setup.py check -s 2>&1 | (! grep -qEi 'error|warning')

lint: black flake8 mypy sdist-check

# ---- Unit Tests (no algod) ---- #

# Slow test which are fast enough on python 3.11+
test-unit-slow: 
	pytest tests/unit/sourcemap_constructs311_test.py -m serial

test-unit-very-slow: 
	pytest tests/unit/sourcemap_constructs_allpy_test.py -m serial

test-unit-async:
	pytest -n auto --durations=10 pyteal tests/unit -m "not slow" -m "not serial"

# Run tests w/ @pytest.mark.serial under ~/tests/unit each in its own proc:
test-unit-sync: test-unit-slow
	find tests/unit -name '*_test.py' | sort | xargs -t -I {} pytest --suppress-no-test-exit-code --dist=no --durations=10 {} -m serial -m "not slow"

test-unit: test-unit-async test-unit-sync

lint-and-test: check-generate-init lint test-unit

# ---- Integration Tests (algod required) ---- #

algod-start:
	docker compose up -d algod --wait

algod-version:
	docker compose exec algod goal --version

algod-start-report: algod-start algod-version

algod-stop:
	docker compose stop algod

test-integ-async:
	pytest -n auto --durations=10 -sv tests/integration -m "not serial"

# Run tests w/ @pytest.mark.serial under ~/tests/integration each in its own proc:
test-integ-sync:
	find tests/integration -name '*_test.py' | sort | xargs -t -I {} pytest --suppress-no-test-exit-code --dist=no --durations=10 {} -m serial

test-integration: test-integ-async test-integ-sync

all-sync: test-unit-sync test-integ-sync

all-lint-unit-integ: lint-and-test test-integration

# ---- Github Actions 1-Liners ---- #

setup-build-test: setup-development lint-and-test

algod-integration: algod-start setup-development test-integration algod-stop

check-code-changes:
	git config --global --add safe.directory /__w/pyteal/pyteal
	[ -n "$$(git log --since='24 hours ago')" ] && (echo "should_run=true" >> $(GITHUB_ENV)) || (echo "should_run=false" >> $(GITHUB_ENV))

nightly-slow: test-unit-very-slow

# ---- Local Github Actions Simulation via `act` ---- #
# assumes act is installed, e.g. via `brew install act`

ACT_JOB = run-integration-tests
local-gh-job:
	act -j $(ACT_JOB)

local-gh-simulate:
	act

# ---- Extras ---- #

coverage:
	pytest --cov-report html --cov=pyteal

sourcemap-coverage:
	pytest --cov-report html --cov=pyteal.stack_frame --cov=pyteal.compiler.sourcemap --cov=pyteal.compiler.compiler --dist=no tests/unit/sourcemap_monkey_unit_test.py -m serial
