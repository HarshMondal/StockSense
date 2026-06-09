# Convenience targets. PYTHONPATH is cleared so a sourced ROS/conda env on the
# developer's machine can't leak pytest plugins into the test run.
PY := .venv/bin/python

.PHONY: test run migrate reset-checkpoints train

test:
	PYTHONPATH= $(PY) -m pytest -q

run:
	DJANGO_SETTINGS_MODULE=stocksense_backend.settings.dev \
		.venv/bin/uvicorn stocksense_backend.asgi:application --host 0.0.0.0 --port 8000 --reload

migrate:
	$(PY) manage.py migrate

reset-checkpoints:
	$(PY) manage.py reset_checkpoints --all-default

train:
	$(PY) manage.py start_trainer
