# SQL scripts to trigger CDC events

This example assumes you are running MySQL in a docker container and therefore you might not have a local mysql client. 

These scripts connect to the MySQL docker container and execute the SQL on that container. 

```sh add_customers.sql``` adds 5 customers in a single transaction.
```sh delete_customers.sql`` deletes any customers with an id > 1004
```sh many_changes.sql``` performs 150 SQL operations, deletes and inserts into the customers table.
```sh update_customers.sql```updates all customers, changes first_name to upper(first_name)
```sh reset_customers.sql``` deletes any customer with an id > 1004

## Using these scripts

If you have ```kafka_consumer_demo.py``` or ```kafka_reader_ESDB_writer.py``` running and want to see event activity in the console, or in EventStoreDB running one or more of these scripts will show activity.

If you are running either of the analysis.. programs, and want to see more data in the graphs, run ```sh many_changes.sql``` followed by ```sh update_customers.sql``` or some combination of the available scripts. 