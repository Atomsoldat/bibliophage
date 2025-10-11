#!/bin/bash

PG_HOST=vectordb.bibliophage.irminsul
PG_PORT=5432
PG_DB_NAME=vectors
PG_USER=bibliophage
PG_PASSWORD=$(kubectl -n bibliophage get secret bibliophage-app-user -o jsonpath='{.data.password}' | base64 -d)

# when we use a "normal" connection string, sqlalchemy may fall back to psycopg2 instead of psycopg3
#export PG_CONNECTION_STRING="postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DB_NAME}"
export PG_CONNECTION_STRING="postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DB_NAME}"

# if we run these using a shebang, we end up with the
# OS python env, so that's no good
python ./server.py
