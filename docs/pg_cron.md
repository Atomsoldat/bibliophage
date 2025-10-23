kubectl -n bibliophage exec bibliophage-documents-1 -- psql -U postgres -d documents -c "SELECT * FROM cron.job;"
kubectl -n bibliophage exec bibliophage-documents-1 -- psql -U postgres -d postgres -c "SHOW cron.database_name;"
