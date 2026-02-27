.PHONY: clean testclean distclean coverageclean cacheclean nuke tailwind docclean upgrade-tailwind tailwind-watch install run set-env create-env

TAILWINDDIR=src/argus/htmx/tailwindtheme
STATICDIR=src/argus/htmx/static
PYTHONPATH=./src


ifneq ($(filter set-env create-env,$(MAKECMDGOALS)),)
  ENV_NAME := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  ifneq ($(ENV_NAME),)
    $(eval $(ENV_NAME):;@:)
  endif
endif

set-env:
ifdef ENV_NAME
	@if [ ! -f ".env.$(ENV_NAME)" ]; then echo "Error: .env.$(ENV_NAME) not found"; exit 1; fi
	@if [ -f .env ] && [ ! -L .env ]; then echo "Error: .env is a regular file, rename it first (e.g. mv .env .env.default)"; exit 1; fi
	@ln -sf ".env.$(ENV_NAME)" .env
	@echo "Selected .env.$(ENV_NAME)"
else
	@echo "Available environments:"
	@ls -1 .env.* 2>/dev/null | grep -v '\.env\.template$$' | sed 's/\.env\./  /' || echo "  (none)"
	@if [ -L .env ]; then echo "\nActive: $$(readlink .env)"; fi
	@echo "\nUsage: make set-env <name>"
endif

create-env:
ifndef ENV_NAME
	@echo "Usage: make create-env <name>"
else
	@if [ -f ".env.$(ENV_NAME)" ]; then echo "Error: .env.$(ENV_NAME) already exists"; exit 1; fi
	@cp .env.template ".env.$(ENV_NAME)"
	@echo "Created .env.$(ENV_NAME) from template"
endif

install:
	uv sync --extra dev

run:
	uv run manage.py runserver


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

tailwind:
	$(TAILWINDDIR)/tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css

tailwind-watch:
	$(TAILWINDDIR)/tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css --watch

upgrade-tailwind:
	PYTHONPATH=$(PYTHONPATH) python3 src/argus/htmx/tailwindtheme/get_tailwind.py
