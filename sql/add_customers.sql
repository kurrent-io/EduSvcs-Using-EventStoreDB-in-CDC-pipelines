 docker exec mysql mysql -umysqluser -pmysqlpw inventory -e '
insert into customers VALUES (NULL, "jack","jones","jj@nowhere.com"),(NULL, "amir","assam","aa@nowhere.com"),(NULL, "Alejandro","Guitierezz","ag@nowhere.com"),(NULL, "cerise","garan","cg@nowhere.com"),(NULL, "Jorge","vallejo","jv@nowhere.com");'
