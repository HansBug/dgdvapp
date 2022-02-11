.PHONY: all build clean

GUI_PYS := \
	main_window_ui.py \
	dialog_config_ui.py \
	form_generate_ui.py

all: build
build: ${GUI_PYS}
clean:
	rm -rf ${GUI_PYS}

%_ui.py: %.ui
	python -m PyQt5.uic.pyuic "$<" -o "$@"
