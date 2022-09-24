
```shell script
pip install grpcio
pip install grpcio-tools
pip install grpcio-reflection

python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. goods_server.proto
```
