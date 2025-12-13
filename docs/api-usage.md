`protoc` determines the API-Paths of the Services we define in our `.proto` files based on their names and package names. We can then see the resulting endpoints in e.g. `python-server/src/bibliophage/v1alpha1/document_connect.py`. Notice how there is a dictionary for service endpoints and a separate  property for the mount path of the service (which the endpoints live under).


When the Python Server runs, we can try reaching it via the following command:

```bash
curl -v \
  -X POST http://localhost:8000/bibliophage.LoadingService/LoadPDF \
  -H "Content-Type: application/json" \
  -d '{}'
```

Reaching the Document service:
```bash
curl -v \
  -X POST http://localhost:8000/bibliophage.DocumentService/StoreDocument \
  -H "Content-Type: application/json" \
  -d '{}'
```

Basic Search (All PDFs)
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha2.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{}'
```

Search by Title
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha2.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{
      "titleQuery": "Player"
    }'
```

Search by System
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha2.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{
      "systemFilter": "PF1E"
    }'
```
