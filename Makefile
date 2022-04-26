# ---- Setup ---- #

setup-development:
	pip install -e .[development]

setup-docs: setup-development
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
	make html && \
	doc2dash --name pyteal --index-page index.html --online-redirect-url https://pyteal.readthedocs.io/en/ _build/html && \
	tar -czvf pyteal.docset.tar.gz pyteal.docset

# ---- Code Quality ---- #

check-generate-init:
	python -m scripts.generate_init --check

ALLPY = docs examples pyteal scripts tests utils *.py
black:
	black --check $(ALLPY)

flake8:
	flake8 $(ALLPY)

# TODO: add `tests` and `utils` to $MYPY when graviton respects mypy (version 🐗) 
MYPY = pyteal scripts
mypy:
	mypy $(MYPY)

lint: black flake8 mypy

# ---- Unit Tests (no algod) ---- #

UNIT = pyteal tests/unit utils
test-unit:
	pytest $(UNIT)

build-and-test: check-generate-init lint test-unit

# ---- Integration Test (algod required) ---- #

sandbox-dev-up:
	docker-compose up -d algod

sandbox-dev-stop:
	docker-compose stop algod

# TODO: set NUM_PROCS = auto when the following issue has been fixed https://github.com/algorand/pyteal/issues/199
NUM_PROCS = 1 
integration-run:
	pytest -n $(NUM_PROCS) --durations=10 -sv tests/integration

test-integration: integration-run

all-tests: build-and-test test-integration

# ---- Local Github Actions Simulation via `act` ---- #

act-apps-install:
	sudo apt update -y
	sudo apt install -y curl git nodejs
	sudo apt -y install ca-certificates curl gnupg lsb-release
	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	sudo echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
	sudo apt update
	sudo apt -y install docker-ce docker-ce-cli containerd.io
	sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	sudo chmod +x /usr/local/bin/docker-compose
	sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
	docker-compose --version


# assumes act is installed, e.g. via `brew install act`:
ACT_JOB = run-integration-tests
local-gh-job:
	act -j $(ACT_JOB)

local-gh-simulate:
	act


# ---- Extras ---- #

coverage:
	pytest --cov-report html --cov=pyteal
