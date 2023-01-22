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

bundle-docs: bundle-docs-clean
	cd docs && \
	make html SPHINXOPTS="-W --keep-going" && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

# ---- Code Quality ---- #

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples pyteal scripts tests *.py
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

NUM_PROCS = auto
test-unit-async:
	pytest -n $(NUM_PROCS) --durations=10 pyteal tests/unit -m "not serial"

# TODO: add blackbox_test.py to multithreaded tests when following issue has been fixed:
# 	https://github.com/algorand/pyteal/issues/199
# Running all the tests under tests/unit synchronously 1 at a time, 
#	and only those with @pytest.mark.serial:
test-unit-sync:
	find tests/unit/ -name '*_test.py' | sort | xargs -t -n1 pytest --dist=no --durations=10 -m serial  2>&1 | grep -v "no tests collected" || true

test-unit: test-unit-async test-unit-sync

lint-and-test: check-generate-init lint test-unit

# ---- Integration Tests (algod required) ---- #

algod-start:
	docker compose up -d algod --wait

algod-stop:
	docker compose stop algod

test-integ-async:
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration -m "not serial"

test-integ-sync:
	find tests/integration -name '*_test.py' | sort | xargs -t -n1 pytest -v --dist=no --durations=10 -m serial 2>&1 | grep -v "no tests collected" || true
	# find tests/integration/sourcemap_monkey_integ_test.py  -name '*_test.py' | sort | xargs -n1 pytest --dist=no --durations=10 -m serial 
	# find tests/integration/algod_test.py | sort | xargs -t -n1 pytest -v --dist=no --durations=10 -m serial 2>&1 | grep -v "no tests collected" || true

test-integration: test-integ-async test-integ-sync

all-sync: test-unit-sync test-integ-sync

all-lint-unit-integ: lint-and-test test-integration

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

refactor-test:
	pytest tests/unit/sourcemap_monkey_unit_test.py
	python tests/sourcemapping/private/goracle01.py > tests/sourcemapping/goracle01.teal
	cd tests/sourcemapping/private && (python goracle01.py || 0) && cd -
	# python tests/sourcemapping/public/decipher_poll_dapp.py > tests/sourcemapping/public/decipher_approval.teal
	# diff tests/sourcemapping/goracle01.teal tests/sourcemapping/goracle01_FIXED.teal
	# diff tests/sourcemapping/public/decipher_approval.teal tests/sourcemapping/public/decipher_approval_FIXED.teal

profiler:
	echo "TODO"

