
## pymupdf
- output looks good
- pymupdf is single threaded, which becomes a problem in large documents (rule books). The developers mention some ways to use multiprocessing to alleviate this somewhat,  but those require [custom code](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html)

## docling
- docling supports multithreading out of the box, as well as [many other settings](https://docling-project.github.io/docling/usage/advanced_options/) and [features](https://docling-project.github.io/docling/usage/enrichments/), such as interpreting images.

- docling supports [using the GPU](https://docling-project.github.io/docling/usage/gpu/)
- Here's someone who implemented a [progress indicator](https://github.com/docling-project/docling/issues/1069#issuecomment-3076645263)

- https://docling-project.github.io/docling/concepts/
- https://docling-project.github.io/docling/examples/
- we might take a look at structured data extraction and image comprehension
