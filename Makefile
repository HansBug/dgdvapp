.PHONY: test unittest docs pdocs run_dev build clean

DOC_DIR     := ./docs
TEST_DIR    := ./test
SRC_DIR     := ./app
SRC_GUI_DIR := ${SRC_DIR}/gui/ui

RANGE_DIR      ?= .
RANGE_TEST_DIR := ${TEST_DIR}/${RANGE_DIR}
RANGE_SRC_DIR  := ${SRC_DIR}/${RANGE_DIR}

IMAGE_DEV   ?= python:3.6.3
IMAGE_SHELL ?= /bin/bash
COV_TYPES   ?= xml term-missing

test: unittest

unittest:
	pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},)

run_dev:
	docker run -it \
		-v $$PWD:$$PWD:rw -w $$PWD \
		--net=host \
		${IMAGE_DEV} \
		${IMAGE_SHELL}

docs:
	$(MAKE) -C "${DOC_DIR}" build
pdocs:
	$(MAKE) -C "${DOC_DIR}" prod

ui:
	$(MAKE) -C "${SRC_GUI_DIR}" build
build:
	pyinstaller -D -F -n app -w app_cli.py
clean:
	rm -rf build dist app.spec
	$(MAKE) -C "${SRC_GUI_DIR}" clean

os:
	echo ${OS}