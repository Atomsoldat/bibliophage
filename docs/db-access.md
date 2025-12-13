## Accessing the local development container databases


### FerretDB

Access DB
```bash
mongosh mongodb://postgres:ferretdb_dev@localhost:27017/
```

Count Documents
```bash
mongosh mongodb://postgres:ferretdb_dev@localhost:27017/ --eval 'db = db.getSiblingDB("bibliophage"); db.pdfs.countDocuments({system: "PATHFINDER_1E"})'
```

Get one Document
```bash
mongosh mongodb://postgres:ferretdb_dev@localhost:27017/ --eval 'db = db.getSiblingDB("bibliophage"); db.pdfs.find().limit(1).toArray()'
```

Pass a filter to find 
```bash
mongosh mongodb://postgres:ferretdb_dev@localhost:27017/ --eval 'db = db.getSiblingDB("bibliophage"); db.pdfs.find({system: "PATHFINDER_1E", type: "BESTIARY"})' | less
```

Use a Projection after the filter to only return certain fields
```bash
mongosh mongodb://postgres:ferretdb_dev@localhost:27017/ --quiet --eval 'db = db.getSiblingDB("bibliophage"); db.pdfs.find({system:
      "PATHFINDER_1E"}, {name: 1, system: 1}).toArray()'
```



### pgVector
```bash
psql postgresql://pgvector:pgvector_dev@localhost/pgvector
```

## How to access the databases of the kubernetes development environment


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
