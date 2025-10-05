
```
k -n bibliophage get secret bibliophage-app-user -o jsonpath='{.data.password}' | base64 -d
psql -h vectordb.bibliophage.irminsul -U bibliophage vectors
```
