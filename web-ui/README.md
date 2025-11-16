## Web UI for Bibliophage

This web application serves as the frontend for our ML related Python services. It is written in Vue.js and Typescript, and uses DaisyUI (which is based on Tailwind CSS) for styling. The communication between the frontend and backend works via Connect RPC.



## Recent NodeJS breakage

Looks like the NodeJS people decided to introduce a change that ends up breaking our vite dev server.
- https://github.com/nodejs/node/issues/60704
- https://bbs.archlinux.org/viewtopic.php?id=310171

For now  we work around this by passing the following node option to our vite invocation

```
NODE_OPTIONS="--no-experimental-webstorage"
```
