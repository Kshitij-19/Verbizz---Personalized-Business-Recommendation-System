#!/bin/bash

# Define paths
PROTO_SRC_DIR="./protos"        # Directory containing .proto files
OUT_DIR="./codegen"             # Directory to store the generated Python files

# Create the output directory if it doesn't exist
mkdir -p $OUT_DIR

# Check if the protobuf compiler is installed
if ! [ -x "$(command -v python -m grpc_tools.protoc)" ]; then
  echo "Error: Protobuf compiler (protoc) or grpc_tools is not installed." >&2
  echo "Install it using: pip install grpcio-tools" >&2
  exit 1
fi

# Compile all .proto files in the PROTO_SRC_DIR
for proto_file in $PROTO_SRC_DIR/*.proto; do
  python -m grpc_tools.protoc \
    --proto_path=$PROTO_SRC_DIR \
    --python_out=$OUT_DIR \
    --grpc_python_out=$OUT_DIR \
    $(basename $proto_file)
done

echo "Proto files successfully compiled into $OUT_DIR!"