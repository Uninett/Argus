.PHONY: clean build testclean distclean docclean coverageclean cacheclean nuke tailwindcli tailwind tailwind-watch upgrade-tailwind

STYLE_SOURCES := $(shell find src/argus -name '*.html')
TAILWINDDIR:=src/argus/htmx/tailwindtheme
STATICDIR:=src/argus/htmx/static
PYTHONPATH:=./src

clean:
	-find . -name __pycache__ -print0 | xargs -0 rm -rf
	-find . -name "*.pyc" -print0 | xargs -0 rm -rf
	-find . -name "*.egg-info" -print0 | xargs -0 rm -rf

build: tailwind

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

tailwindcli:
	@which tailwind || echo "tailwindcss not in path"

tailwind: tailwindcli
	tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css

tailwind-watch:
	$(TAILWINDDIR)/tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css --watch

upgrade-tailwind:
	PYTHONPATH=$(PYTHONPATH) python3 src/argus/htmx/tailwindtheme/get_tailwind.py
