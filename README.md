[![lint](https://github.com/ychab/miolingo/actions/workflows/lint.yaml/badge.svg)](https://github.com/ychab/miolingo/actions/workflows/lint.yaml)
[![units](https://raw.githubusercontent.com/ychab/miolingo/badges/.badges/main/units.svg)](https://github.com/ychab/miolingo/actions/workflows/units.yaml)
[![poetry](https://github.com/ychab/miolingo/actions/workflows/poetry.yaml/badge.svg)](https://github.com/ychab/miolingo/actions/workflows/poetry.yaml)
[![django version](https://raw.githubusercontent.com/ychab/miolingo/badges/.badges/main/poetry-django-version.svg)](https://github.com/ychab/miolingo/actions/workflows/version.yaml)

# MioLingo Backend

Miolingo is a project to learn languages, but **YOU** are our own teacher!

This backend is build with [Django](https://www.djangoproject.com/)
and [Django Rest Framework](https://www.django-rest-framework.org/).


## Requirements

* For development, into a **virtualenv** (recommended) :
  * you must first install [poetry](https://python-poetry.org/docs/#installation).
  * Once installed, just run: `poetry install`

* For testing (CI), just do : `pip install -r requirements/test.txt`

* For production, do instead : `pip install -r requirements/prod.txt`

*Note*: For now, only Python 3.10 is tested.

## Databases

Having access with proper permissions for one of the [supported SGDB by Django](https://docs.djangoproject.com/en/dev/ref/databases/).

## Pre-commit

Python binding package should be already installed by Poetry, so you just have
to do:
> pre-commit install

That's it!

**ugly tips**: If you want to skip check for a particular commit, do:
> git commit -m "blabla" --no-verify

but hope this is for good reasons huh!!

## Get started

### Local installation

Once requirements are setup, do the following steps:
````
cp miolingo/settings/local.py.dist miolingo/settings/local.py
vim miolingo/settings/local.py  # edit at least DATABASES and SECRET_KEY !
python manage.py migrate
python manage.py createadmin --password=<PASSWORD>
./manage.py runserver 127.0.0.1:8000
google-chrome http://127.0.0.1:8000/admin &
````

*Tips*: take a look at the Makefile ;-)
