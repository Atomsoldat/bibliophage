Create project skeleton

```bash
yarn create vite vue-ui --template vue-ts
cd vue-ui
yarn install
yarn add bootstrap bootstrap-icons
# runtime dependencies
yarn add @connectrpc/connect @connectrpc/connect-web @bufbuild/protobuf
# buildtime dependencies
yarn add -D @bufbuild/buf @bufbuild/protoc-gen-es @bufbuild/protoc-gen-connect-es
```

Generate API code (buf uses `buf.gen.yaml` for configuration)
```bash
yarn buf generate ../grpc-api
```


Run development webserver
```bash
yarn dev
```

Have yarn look for unsafe / undeclared dependencies and code
```bash
yarn dlx @yarnpkg/doctor
```
