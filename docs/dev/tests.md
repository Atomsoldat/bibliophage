## Python Server Tests


```bash
pixi run pytest tests/test_document_service.py
pixi run pytest tests/test_pdf_service.py
```

We can also execute individual test functions
```
pixi run python -m pytest tests/test_document.py::test_store_document_integration
```

Or we can select the tests to run based on the decorators like `@pytest.mark.unit`
```
pixi run python -m  pytest -v -m unit
pixi run python -m  pytest -v -m "not unit"
```


See [here](https://docs.pytest.org/en/7.1.x/example/markers.html) for more selection tricks
