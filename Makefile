SOURCES=sources/Molander.glyphs
FAMILY=Molander

help:
	@echo "###"
	@echo "# Build targets for $(FAMILY)"
	@echo "###"
	@echo
	@echo "  make build:  Builds the fonts and places them in the fonts/ directory"
	@echo "  make test:   Tests the fonts with fontbakery (Google Fonts profile)"
	@echo "  make clean:  Removes the virtual environment and build files"
	@echo "  make update: Updates pinned requirements from requirements.in"
	@echo

build: build.stamp

venv: venv/touchfile

build.stamp: venv sources/config.yaml $(SOURCES)
	rm -rf fonts
	(for config in sources/config*.yaml; do . venv/bin/activate; gftools builder $$config; done) && touch build.stamp

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

test: build.stamp
	mkdir -p out/fontbakery
	. venv/bin/activate; fontbakery check-googlefonts -l WARN --succinct --html out/fontbakery/fontbakery-report.html --ghmarkdown out/fontbakery/fontbakery-report.md fonts/ttf/*.ttf || echo "::warning file=sources/config.yaml,title=fontbakery failures::Fontbakery reported problems. See out/fontbakery/fontbakery-report.html."

clean:
	rm -rf venv build.stamp out
	find . -name "*.pyc" -delete

update: venv
	venv/bin/pip install --upgrade pip-tools
	venv/bin/pip-compile --upgrade --verbose --resolver=backtracking requirements.in
	venv/bin/pip-sync requirements.txt

.PHONY: help build venv test clean update
