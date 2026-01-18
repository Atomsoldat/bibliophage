Our `CHANGELOG.md` is generated based on the messages of our [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/). We use [cocogitto](https://docs.cocogitto.io/guide/commit.html) to automate this process.

To create a properly formatted commit, execute:

```bash
cog commit TYPE "MESSAGE" [SCOPE]
```


## Versioning

Cocogitto needs an initial version to calculate future version increments from. So we provide the version we want to start at.

```bash
cog bump --version 0.0.0
```

Incrementing versions:
```bash
# trust, but verify
cog bump --auto --dry-run
# actually perform the increment
cog bump --auto
```

See the changelog that would be generated from a `cog bump` invocationL
```bash
cog changelog
```

To rewrite non-conformant commit messages
```bash
cog edit
```


