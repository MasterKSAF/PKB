.PHONY: test migrate downgrade revision current

test:
	py -3.13 -m pytest

migrate:
	py -3.13 -m alembic upgrade head

downgrade:
	py -3.13 -m alembic downgrade base

revision:
	py -3.13 -m alembic revision --autogenerate -m "$(m)"

current:
	py -3.13 -m alembic current
