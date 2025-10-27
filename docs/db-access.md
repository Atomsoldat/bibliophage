## How to access the databases of the development environment


If you want to access the PostgreSQL databases used in the development environment, here's how to do that:
```bash
k -n bibliophage get secret db-standard-user -o jsonpath='{.data.password}' | base64 -d
psql -h vectordb.bibliophage.irminsul -U bibliophage vectors
psql -h documentdb.bibliophage.irminsul -U bibliophage documents
```


And here's the commands to access FerretDB:
```bash
bibliophage_db_pw=$(k -n bibliophage get secret db-standard-user -o jsonpath='{.data.password}' | base64 -d)
mongosh "mongodb://bibliophage:${bibliophage_db_pw}@ferretdb.bibliophage.irminsul:27017/documents"
```
