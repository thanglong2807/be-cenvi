FROM mysql:8.0

ENV MYSQL_DATABASE=cenvi_audit

COPY init.sql /docker-entrypoint-initdb.d/001-init.sql
