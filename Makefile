.PHONY: clean testclean distclean coverageclean nuke tailwind

TAILWINDDIR=src/argus_htmx/tailwindtheme
STATICDIR=src/argus_htmx/static

clean:
	-find . -name __pycache__ -print0 | xargs -0 rm -rf
	-find . -name "*.pyc" -print0 | xargs -0 rm -rf
	-find . -name "*.egg-info" -print0 | xargs -0 rm -rf
	-find . -name ".ruff_cache" -print0 | xargs -0 rm -rf

distclean:
	-rm -rf ./dist
	-rm -rf ./build

coverageclean:
	-rm .coverage
	-rm .coverage.*
	-rm coverage.xml
	-rm -rf htmlcov

testclean: coverageclean clean
	-rm -rf .tox

nuke: clean distclean testclean

tailwind:
	tailwindcss -c $(TAILWINDDIR)/tailwind.config.js -i $(TAILWINDDIR)/styles.css -o $(STATICDIR)/styles.css
