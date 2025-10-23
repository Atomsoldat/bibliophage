
```
k -n bibliophage get secret bibliophage-app-user -o jsonpath='{.data.password}' | base64 -d
psql -h vectordb.bibliophage.irminsul -U bibliophage vectors
psql -h documentdb.bibliophage.irminsul -U bibliophage documents
```

```
bibliophage_db_pw=$(k -n bibliophage get secret bibliophage-app-user -o jsonpath='{.data.password}' | base64 -d)
mongosh "mongodb://bibliophage:${bibliophage_db_pw}@ferretdb.bibliophage.irminsul:27017/"
```
