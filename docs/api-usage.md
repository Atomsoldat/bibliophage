## Talking to the API With grpcurl

If we correctly implement reflection, we can use `grpcurl` to talk to our API (these commands assume the data-server is running locally):

List available services
```
grpcurl -plaintext localhost:50051 list

```

List only one service
```
grpcurl -plaintext localhost:50051 list bibliophage.LoadingService
```

Describe methods, that a given service offers (this gives us the function signature)
```bash
grpcurl -plaintext localhost:50051 describe bibliophage.LoadingService
bibliophage.LoadingService is a service:
service LoadingService {
  rpc LoadPDF ( .bibliophage.PdfLoadRequest ) returns ( .bibliophage.PdfLoadResponse );
}
```


We can then figure out what a `PdfLoadRequest` looks like, so we can construct our query:
```bash
grpcurl -plaintext localhost:50051 describe bibliophage.PdfLoadRequest
bibliophage.PdfLoadRequest is a message:
message PdfLoadRequest {
  string pdf_path = 1;
  string name = 2;
  .bibliophage.RpgSystem system = 3;
  .bibliophage.PublicationType pub_type = 4;
  int32 page_count = 5;
  int32 chunk_size = 6;
  int32 chunk_overlap = 7;
}
```

Query our grpc service with our query
```
grpcurl -plaintext -d '{
    "pdf_origin_path": "pdfs/pf1e/bestiary_bonus.pdf",
    "pdf_name": "Bestiary Bonus",
    "pdf_system": "PATHFINDER_1E",
    "pdf_type": "BESTIARY"
}' localhost:50051 bibliophage.LoadingService/LoadPDF
```
