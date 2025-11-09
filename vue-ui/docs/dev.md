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
