FROM mariadb:11.7.1-ubi9-rc

COPY ddl.sql /docker-entrypoint-initdb.d