 docker exec mysql mysql -umysqluser -pmysqlpw inventory -e 'update customers set first_name = UPPER(first_name)'
