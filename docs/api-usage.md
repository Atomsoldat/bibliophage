`protoc` determines the API-Paths of the Services we define in our `.proto` files based on their names and package names. We can then see the resulting endpoints in e.g. `python-server/src/bibliophage/v1alpha3/document_connect.py`. Notice how there is a dictionary for service endpoints and a separate  property for the mount path of the service (which the endpoints live under).



## Protobuf Idiosyncracies

Protobuf3's "always emit defaults" philosophy differs from JSON's typical explicit-null approach. In protobuf3, absence of a field means "it has the default value" - this saves bandwidth but can be confusing  when on expects explicit zeros/empties. Many APIs enable `include_default_values=True` in production to make responses more predictable for clients, trading message size for clarity.

See:
- https://stackoverflow.com/a/31058885




## Curl

When the Python Server runs, we can try reaching it via the following command:

Basic Search (All PDFs)
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha3.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{}'
```

Search by Title
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha3.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{
      "titleQuery": "Player"
    }'
```

Search by Systems (v1alpha3 uses systemFilters array)
```bash
  curl -X POST http://localhost:8000/bibliophage.v1alpha3.PdfService/SearchPdfs \
    -H "Content-Type: application/json" \
    -d '{
      "systemFilters": ["PATHFINDER_1E"]
    }'
```
