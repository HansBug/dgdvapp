.PHONY: all build clean

all: build
build: main_window_ui.py
%_ui.py: %.ui
	python -m PyQt5.uic.pyuic "$<" -o "$@"

clean:
	rm -rf *_ui.py
