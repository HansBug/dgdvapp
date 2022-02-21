.PHONY: all build clean

RM := rm -rf

PROTOC := $(shell which protoc)

PROTO_FILES := \
	mps_coordinate.proto \
	mps_evaluation.proto \
	mps_message.proto
PB2_PY_FILES := $(addsuffix _pb2.py, $(basename ${PROTO_FILES}))

all: build
build: ${PB2_PY_FILES}
clean:
	$(RM) ${PB2_PY_FILES}

%_pb2.py: %.proto
	$(PROTOC) -I=./ --python_out=./ "$<"

