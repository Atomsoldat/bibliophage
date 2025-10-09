## Talking to the API With grpcurl

If we correctly implement reflection, we can use `grpcurl` to talk to our API:

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
  rpc LoadPDF ( .bibliophage.LoadRequest ) returns ( .bibliophage.LoadResponse );
}
```


We can then figure out what a `LoadRequest` looks like, so we can construct our query:
```bash
grpcurl -plaintext localhost:50051 describe bibliophage.LoadRequest
bibliophage.LoadRequest is a message:
message LoadRequest {
  string pdf_path = 1;
  string name = 2;
  .bibliophage.RpgSystem system = 3;
  .bibliophage.PublicationType pub_type = 4;
  int32 page_count = 5;
  int32 chunk_size = 6;
  int32 chunk_overlap = 7;
}
```

Query our grpc service with out query
```
grpcurl -plaintext -d '{
    "pdf_path": "pdfs/pf1e/bestiary_bonus.pdf",
    "name": "Bestiary Bonus",
    "system": "PATHFINDER_1E",
    "pub_type": "BESTIARY"
}' localhost:50051 bibliophage.LoadingService/LoadPDF

```
