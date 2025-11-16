Create project skeleton

```bash
yarn create vite vue-ui --template vue-ts
cd vue-ui
yarn install
yarn add bootstrap bootstrap-icons
# runtime dependencies
yarn add @connectrpc/connect @connectrpc/connect-web @bufbuild/protobuf
# buildtime dependencies
yarn add -D @bufbuild/protoc-gen-es @bufbuild/protoc-gen-connect-es
```
