Run development webserver
```bash
yarn dev
```

Have yarn look for unsafe / undeclared dependencies and code
```bash
yarn dlx @yarnpkg/doctor
```

We use a script in our `package.json` to execute [knip](https://knip.dev/), which helps find unused dependencies.
```
yarn knip
```


## Debugging

- https://devtools.vuejs.org/
- https://devtools.vuejs.org/guide/vite-plugin

In Vite, `ALT + SHIFT + D` will  open the debugger panel


### Standalone application

In case we are using an unsupported browser or our application is packaged in a way that does not use a browser (Electron), we can use a standalone application for debugging instead. The standalone  debugger starts a webserver presenting a script, which we can load from our application. To do that, we need to add the following to the `<head>` element of our applications's HTML file.

```
<script src="http://localhost:8098"></script>
```
