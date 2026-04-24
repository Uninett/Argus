.PHONY: clean testclean distclean coverageclean cacheclean nuke setup-tailwind tailwind-config tailwind-build-config tailwind docclean upgrade-tailwind tailwind-watch check-test-names sync

TAILWINDDIR=src/argus/htmx/tailwindtheme
STATICDIR=src/argus/htmx/static
PYTHONPATH=./src


clean:
	-find . -name __pycache__ -print0 | xargs -0 rm -rf
	-find . -name "*.pyc" -print0 | xargs -0 rm -rf
	-find . -name "*.egg-info" -print0 | xargs -0 rm -rf

cacheclean:
	-find . -name ".ruff_cache" -print0 | xargs -0 rm -rf

distclean:
	-rm -rf ./dist
	-rm -rf ./build

docclean:
	-rm -rf ./docs/_build

coverageclean:
	-rm .coverage
	-rm .coverage.*
	-rm coverage.xml
	-rm -rf htmlcov

testclean: coverageclean clean
	-rm -rf .tox

nuke: clean docclean distclean testclean cacheclean

setup-tailwind: upgrade-tailwind tailwind-config tailwind

tailwind-config:
	PYTHONPATH=$(PYTHONPATH) python3 manage.py tailwind_config

tailwind-build-config:
	PYTHONPATH=$(PYTHONPATH) python3 src/argus/htmx/tailwindtheme/generate_css_config.py

tailwind:
	$(TAILWINDDIR)/tailwindcss -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css

tailwind-watch:
	$(TAILWINDDIR)/tailwindcss -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css --watch

upgrade-tailwind:
	PYTHONPATH=$(PYTHONPATH) python3 src/argus/htmx/tailwindtheme/get_tailwind.py

sync:
ifndef VIRTUAL_ENV
	$(error Run this command inside a virtual environment)
endif
	pip3 install -r requirements.txt -e ".[dev]"

check-test-names:
	python3 checks/check_test_names.py --base main
