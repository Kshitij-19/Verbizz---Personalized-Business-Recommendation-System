@echo off
set PROTO_SRC_DIR=./protos
set OUT_DIR=./codegen

:: Create the output directory if it doesn't exist
if not exist %OUT_DIR% (
    mkdir %OUT_DIR%
)

:: Check if grpc_tools is installed
python -m grpc_tools.protoc --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo "Error: Protobuf compiler (protoc) or grpc_tools is not installed."
    echo "Install it using: pip install grpcio-tools"
    exit /b 1
)

:: Compile all .proto files in the PROTO_SRC_DIR
for %%f in (%PROTO_SRC_DIR%\*.proto) do (
    python -m grpc_tools.protoc ^
        --proto_path=%PROTO_SRC_DIR% ^
        --python_out=%OUT_DIR% ^
        --grpc_python_out=%OUT_DIR% ^
        %%f
)

echo "Proto files successfully compiled into %OUT_DIR%!"
