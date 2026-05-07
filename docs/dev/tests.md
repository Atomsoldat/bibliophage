## Python Server Tests


```bash
pixi run pytest tests/test_document_service.py
pixi run pytest tests/test_pdf_service.py
```

We can also execute individual test functions
```
pixi run python -m pytest tests/test_document.py::test_store_document_integration
```
