all:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

help: all

pre:
	pre-commit run -a

lint:
	black --diff --check miolingo
	pylama miolingo
	isort --diff --check miolingo

deps:
	poetry show --outdated
	npm outdated

poetry:
	poetry update
	poetry lock
	poetry export -f requirements.txt --only main -o requirements/prod.txt
	poetry export -f requirements.txt --with test -o requirements/test.txt
	poetry export -f requirements.txt --with test,dev -o requirements/dev.txt

npm:
	npm update
	npm run dist

drop_db:
	psql -U postgres -c "DROP DATABASE miolingo"

create_db_user:
	psql -U postgres -c "CREATE USER miolingo WITH encrypted password 'miolingo' SUPERUSER"

create_db:
	psql -U postgres -c "CREATE DATABASE miolingo OWNER miolingo"

migrate:
	python manage.py migrate

admin:
	python manage.py createadmin --password=admin

trans:
	cd miolingo && python ../manage.py makemessages -d django -l en -l fr
	cd miolingo && python ../manage.py makemessages -d djangojs -l en -l fr
	cd miolingo && python ../manage.py compilemessages -l en -l fr

data:
	python manage.py importtrans fr-es.csv fr es admin

reset: drop_db create_db migrate admin data
