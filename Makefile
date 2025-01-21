.PHONY: clean testclean distclean coverageclean cacheclean nuke tailwind docclean

TAILWINDDIR=src/argus/htmx/tailwindtheme
STATICDIR=src/argus/htmx/static

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
	tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css
