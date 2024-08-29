 docker exec mysql mysql -umysqluser -pmysqlpw inventory -e 'delete from customers where id > 1004'
