# Changelog
All notable changes to this project will be documented in this file. See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

- - -
## 0.0.0 - 2026-01-18
### Packages
- web-ui locked to 0.0.0
- python-server locked to 0.0.0
### Global changes
#### Features
- add RAG related fields to chat related proto3 messages - (d91c0f5) - Leon Welchert
- allow filtering documents by system using ANY matching on the server side - (d4ed985) - Leon Welchert
- remove unnecessary resource reservation for gpus in docker compose file - (6186a73) - Leon Welchert
- Add Document Embedding Modal to Library view - (ab47dc6) - Leon Welchert
- add new chat rpc api for llm integration - (00280f8) - Leon Welchert
- extend document API to also handle PDFs in v1alpha3 - (7cb689b) - Leon Welchert
- define new api version v1alpha3, adressing accumulated TODOs - (9f20bd7) - Leon Welchert
- extend document api to use and provide document source information - (a879447) - Leon Welchert
- add ollama container managed by Tilt - (5a72626) - Leon Welchert
- add optional content field to PDF api messages for transporting the entirety of a loaded document - (eb8c5f5) - Leon Welchert
- Display PDF Search Results as Table in Document List View - (dad291a) - Leon Welchert
- mostly get PDF search working - (93aa9aa) - Leon Welchert
- Set up basic database services for development - (35a407e) - Leon Welchert
- define v1alpha2 API schema - (d8d4817) - Leon Welchert
- add Tiltfile - (aba888f) - Leon Welchert
- replace django web ui with vue based web ui - (658aa27) - Leon Welchert
- mock up python server RPC Connect usage - (2240991) - Leon Welchert
- add vue dev tools and document how to use it with vite and without - (e7d903f) - Leon Welchert
- continue vue -> python-server api usage implementation - (5d01ad1) - Leon Welchert
- start working on API usage for PDF uploading - (164746c) - Leon Welchert
- add connect-web library - (2442806) - Leon Welchert
- add knip for finding redundant dependencies, remove redundant dependencies - (e81f188) - Leon Welchert
- add Makefile command for generating rpc api in vue-ui - (ec86518) - Leon Welchert
- add basic Makefile for project scope tasks - (f063209) - Leon Welchert
- POC II vue web ui - (531a003) - Leon Welchert
- POC vue web  ui - (0f77b2d) - Leon Welchert
- rename web-ui and data-server applications - (6344b99) - Leon Welchert
- extend API for document storage- Add new API objects for document storage- update web-ui side of api code - (7bc803e) - Leon Welchert
- add django server for accessing  langchain server api - (d90937f) - Leon Welchert
- make the server actually load pdfs and store them as vectors - (2125ff2) - Leon Welchert
- Throw together a grpc server that pretends to load PDFs - (3c40cde) - Leon Welchert
- come up with draft for pdf loading server API - (3bc6f07) - Leon Welchert
- Jedem Anfang wohnt ein Zauber inne - (ce27d8b) - Leon Welchert
#### Bug Fixes
- fix pgvector init script permissions - (266d2dc) - Leon Welchert
- Fix old sql-alchemy related connection strings to work with psycopg and consolidate python server env in Tiltfile - (4f42bef) - Leon Welchert
- fix ollama health check - (9479695) - Leon Welchert
- properly return a list of matching pdfs when using search_pdfs function in loading service - (b46323d) - Leon Welchert
- correctly configure ferretdb connection parameters - (46f9991) - Leon Welchert
- do not provide full document content in search responses - (112237f) - Leon Welchert
- work around recent NodeJS 25.2 breakage https://github.com/nodejs/node/issues/60704 - (0beaca5) - Leon Welchert
- prefix http:// protocol to URL for connect transport instantiation - (b0f5643) - Leon Welchert
- handle undefined PDF file and file name during PDF upload - (4857d81) - Leon Welchert
- downgrade grpc libraries in webui - (158265e) - Leon Welchert
- rename core django application to not collide with the overall project name - (7975ee9) - Leon Welchert
#### Documentation
- add cocogitto configuration file - (ab4f7eb) - Leon Welchert
- document docker-compose requirement - (94b578e) - Leon Welchert
- remove references to old API versions from documentation - (a9aadd2) - Leon Welchert
- fix dumb formulation - (b96b492) - Leon Welchert
- document manual api code regeneration - (3a8d6e6) - Leon Welchert
- document future api adjustment for PDF deletion - (ff6e8ff) - Leon Welchert
- document potential for future API consolidation - (a04662e) - Leon Welchert
- document future necessity for PDF API adjustment for multi-system or system agnostic PDFs - (a9b24fb) - Leon Welchert
- reference actual technical installation instructions for build tools rather than the flashy landing pages - (b4cab4a) - Leon Welchert
- document PDF API usage - (6c8693c) - Leon Welchert
- Update README.md to explain new tilt based development environment - (4f5d687) - Leon Welchert
- document anecdote about fitz/pymupdf name - (aff0c8e) - Leon Welchert
- document some thoughts about pdf processing - (e39fd6c) - Leon Welchert
- document local container db access - (3cb3b69) - Leon Welchert
- document some reading material on writing protobuf based APIs - (17630ce) - Leon Welchert
- document API structure - (abbc300) - Leon Welchert
- remove old grpc documentation - (8ed34d0) - Leon Welchert
- add info about Connect api to README.md - (725d3dd) - Leon Welchert
- update README.md - (3d6d4f1) - Leon Welchert
- replace default README.md with some basic information on the new web-ui - (86c56a1) - Leon Welchert
- document application structure and typescript - Vue interaction - (11856d8) - Leon Welchert
- add documentation for common dev procedures - (2f74f5d) - Leon Welchert
- document connect rpc generation for typescript - (28106f6) - Leon Welchert
- document usage of databases and the grpc API - (e3716ff) - Leon Welchert
#### Tests
- add rough draft for python server tests - (9e58820) - Leon Welchert
#### Refactoring
- remove unnecessary chunking configuration from PDF API and add embedding API - (82633d1) - Leon Welchert
- move dev container files to more appropriately named directory - (4bff289) - Leon Welchert
- remove redundant pdf api messages that were replaced by the document API - (7f4e0b4) - Leon Welchert
- remove references to old API version v1alpha2 - (2a753e3) - Leon Welchert
- tidy up v1alpha3 API - (aa09826) - Leon Welchert
- rename property for matches returned by document search to more clearly represent their meaning - (39c8314) - Leon Welchert
- modify API to allow reusing document filter messages - (3861c18) - Leon Welchert
- move python code in python-server to src - (df297fd) - Leon Welchert
- refactor python server configuration to be read from environment and store in class - (82b23e6) - Leon Welchert
- restructure api directory structure for schema versioning - (0e299ef) - Leon Welchert
- move api generation scripts to service directories - (6af1a95) - Leon Welchert
#### Miscellaneous Chores
- commit  .tiltignore - (dfc6c95) - Leon Welchert
- add directories to .gitignore - (973389a) - Leon Welchert
- add some documentation for using handling the documents database - (3c9dd5e) - Leon Welchert
- Make README.md actually informative - (988544d) - Leon Welchert
- add some illuminating comments - (38d8173) - Leon Welchert
- move pdf loading server to separate directory - (0e0c5b5) - Leon Welchert
- move grpc stuff to subdir for improved tidiness - (f3aeac3) - Leon Welchert
- Add python cache to gitignore - (2925c36) - Leon Welchert
#### Style
- reformat API protobuf code - (5d008ec) - Leon Welchert
- move api code formatting over to tilt - (6251f15) - Leon Welchert
- reformat protobuf specification using buf format - (9ef4332) - Leon Welchert

- - -

Changelog generated by [cocogitto](https://github.com/cocogitto/cocogitto).