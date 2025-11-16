When the Python Server runs, we can try reaching it via the following command:

```bash
curl -v \
  -X POST http://localhost:8000/bibliophage.LoadingService/LoadPDF \
  -H "Content-Type: application/json" \
  -d '{}'
```
