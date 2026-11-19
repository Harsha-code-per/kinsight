PY ?= python
FHIR_URL ?= http://127.0.0.1:8088/fhir
.PHONY: test lint cohort demo up fhir-seed
test:
	$(PY) -m pytest -q
lint:
	$(PY) -m ruff check services tests
cohort:
	$(PY) scripts/make_demo_cohort.py
demo:
	$(PY) scripts/demo.py
up:
	docker compose up --build
fhir-seed:
	$(PY) -m scripts.export_fhir_bundles --upload "$(FHIR_URL)"
