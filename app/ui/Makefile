.PHONY: all build clean

RM := rm -rf

PYTHON := $(shell which python)
PYUIC5 := $(PYTHON) -m PyQt5.uic.pyuic

UI_FILES := \
	main_window.ui \
	dialog_config.ui \
	form_generate.ui \
	form_log_process.ui \
	form_metrics.ui
GUI_PY_FILES := $(addsuffix _ui.py, $(basename ${UI_FILES}))

all: build
build: ${GUI_PY_FILES}
clean:
	$(RM) ${GUI_PY_FILES}

%_ui.py: %.ui
	$(PYUIC5) "$<" -o "$@"
