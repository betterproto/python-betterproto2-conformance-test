FROM ubuntu:22.04

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y wget build-essential git python3 python3-dev
RUN apt-get install -y python3-venv python3-pip

# Install protobuf
RUN git clone https://github.com/protocolbuffers/protobuf/ --depth 1 --branch v29.3
WORKDIR /protobuf

# Install bazel
RUN wget https://github.com/bazelbuild/bazelisk/releases/download/v1.25.0/bazelisk-amd64.deb
RUN apt-get install -y ./bazelisk-amd64.deb
RUN rm bazelisk-amd64.deb
RUN bazel --version

# Install betterproto in a virtual environment
WORKDIR /protobuf/conformance
RUN python3 -m venv .venv
RUN ./.venv/bin/pip install betterproto2-compiler grpcio-tools
ENV PATH="/protobuf/conformance/.venv/bin:$PATH"

# Run the standard Python test
RUN bazel test --verbose_failures //python:conformance_test

# Compile the test files
RUN mkdir lib
RUN python -m grpc_tools.protoc -I . --python_betterproto2_out=lib conformance.proto
RUN cp ../src/google/protobuf/test_messages_proto3.proto . && python -m grpc_tools.protoc -I . --python_betterproto2_out=lib test_messages_proto3.proto

# Get the betterproto2 conformance file
RUN git clone https://github.com/betterproto/python-betterproto2-conformance-test
RUN cp python-betterproto2-conformance-test/conformance_python.py .

# Run the test again
CMD bazel test --verbose_failures --test_output=all --experimental_ui_max_stdouterr_bytes=1073741819 //python:conformance_test > /mount/stdout_output

# cd betterproto2-conformance && git pull && cd .. && cp betterproto2-conformance/conformance_python.py .
