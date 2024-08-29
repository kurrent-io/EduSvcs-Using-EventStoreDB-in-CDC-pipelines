# Change Data Capture (CDC) to Event Store Example using Debezium

This example will show the steps and processes to replicate changes from a MySQL or MariaDB instance into EventStoreDB.

# Architecture Overview

Key tools:
Image of Basic
MySQL=>DBZ=>ESDB

![Image of tools used](./images/excalidraw-animate_slow.svg "Big Picture")

Supporting tools:
MySQL(Binlog)
Kafka(Zookeeper, kafka-connect)
EventStoreDB(projections, correlations(?))

![Image of tools used](./images/big_picture.jpg "The details")

# Discussion

The movement of data from one system to another is a widespread use case. 

Data regularly moves from your operational data store to your data warehouse or data lake. 

(Image and Discussion here)

A frequently used tool to enable this data replication is Debezium,
(Description of DBZ here)

# Features of EventStoreDB

EventStoreDB provides the following functionality.

* Durable and immutable log of events (I don't know what else to call them here)
* Guaranteed ordering of those events
* Ability to subscribe to those events (either globally or more granularly)
* Granular enforcement of consistency guarantees
* Granular access control

Given those features, EventStoreDB can be critical in managing your data flow.

# How this project is structured

This repo summarizes the steps to deploy a POC of a data path from MySQL or MariaDB to EventStoreDB.

Docker implementations are used for each required tool. 

To run this locally, you will need Docker installed. 

Please note that with containers being launched, it takes a fair amount of computing resources.

With that in mind, here are the steps. 

1. Start Zookeeper
2. Start Kafka
3. Start MySQL
4. Start MySQL CLI
5. Start Kafka-Connect
6. Deploy connector (get better definition of this)
7. Deploy a topic watcher
8. Start EventStoreDB
9. Run Python code to read from the Kafka topic and write to EventStoreDB

Most steps are required. The exception is the topic watcher, that provides information about how the process is working up to that point. 


# Let's get started

## 1. Starting Zookeeper 


### What is Zookeeper?

A Zookeeper cluster provides a distributed, consistent, fault-tolerant directory or tree of information. Typical use cases for Zookeeper are configuration management, leader election, message queues, and notification systems. 


### What products use Zookeeper?
The valuable service provided by Zookeeper underpins many projects, with Hadoop and Kafka being the more widely used examples. 


### How does Kafka use Zookeeper?
Kafka uses Zookeeper to track which nodes are available, what topics are being served, etc. 

Kafka requires and uses Zookeeper as a core requirement of providing the Kafka service.


### Will you need to interact directly with Zookeeper for this demo?
No. 

In this example, you don't need to interact directly with Zookeeper, but Kafka requires it, so it is the first service you will need to start. 

However, in the interest of learning how each part of the system works, the Zookeeper instance is started with some useful settings if you want to verify a working Zookeeper quorum. 

The start command to start a Docker instance is below. Note the setting 

``` -e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*" ```
This setting enables 4letterwords, which is useful for checking a Zookeeper quorum's health. 

You pass ZK "ruok" for "Are You Okay" over telnet, and if Zookeeper is running, it will return "imok" for "I am okay."

```
docker run -e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*" -it --rm --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 quay.io/debezium/zookeeper:2.7
```


### Shell script alternative to cut and paste

Since cutting and pasting commands can sometimes lead to accidental introduction of newlines, or other characters, a shell script is provided as part of this repo. (Put this in the header)

You can run ```sh 01_zookeper.sh```

Note that the Docker container is started in a way that maintains control of the terminal that launched it; this is expected behavior. 


### Ports Required by Zookeeper

Note that this uses ports 2181, 2888, and 3888 and will fail to start if other services are using those ports.


### Verifying Zookeeper is running

You can ask Zookeeper, "Are you okay?"

```
echo ruok | nc -v localhost 2181 ;echo
```

Your response should be "imok".
```
Connection to localhost port 2181 [tcp/eforward] succeeded!
imok
```

You can ask for configuration and statistics.

```
echo stat | nc -v localhost 2181 ;echo
```

```
$ echo conf | nc -v localhost 2181 ;echo
```


### If you have issues:
This command works with this version of Zookeeper and this Docker container. 

If you want to use another version of Zookeeper or another Docker container, you may need to change this "-e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*"". This is one way to turn on the 4letter words functionality. You probably do not require 4letter words, but they are used here to validate that Zookeeper is working. 

Insert-ruok example--


## 2. Starting Kafka

You can start Kafka with the following command.

```
docker run -it --rm --name kafka -p 9092:9092 -e ADVERTISED_HOST_NAME=<YOUR_HOSTNAME_OR_IP_ADDRESS> --link zookeeper:zookeeper quay.io/debezium/kafka:2.7
```
Points to note...

Kafka needs to know your laptop's hostname for the Python application to connect to it. The other Docker instances are on the same Docker network due to the—- link setting, but the Python example will require your laptop to connect. Setting the advertised host name is one way to enable that connection.

The shell script uses the value returned from the command. 
```
ipconfig getifaddr en0
```

If that command does not work on your computer, edit it to include your IP address. 

You can test the command below in a terminal if you have issues. 

```
echo ADVERTISED_HOST_NAME=$(ipconfig getifaddr en0)
ADVERTISED_HOST_NAME=192.168.1.14
```

Note that this uses port 9092 and will fail if that port is not available.

The ```--link zookeeper:zookeeper``` allows this container to see the Zookeeper container as if they were on the same network.


### Optional: Verify Kafka has registered with Zookeeper

The Zookeeper container will have an instance of the Zookeeper Command Line Client (zkCli.sh)

If you want to explore and verify that Kafka has found Zookeeper, you can run the following commands.

1. Connect to the instance

```docker exec -it zookeeper sh```

2. Launch the zkCli

 ```/zookeeper/bin/zkCli.sh```

3. List the Kafka brokers id's

``` ls /brokers/ids```
[1]

This shows that Kafka is connected and registered with ZK quorum.

If you stopped Kafka and see the list go to 0

```
[zk: localhost:2181(CONNECTED) 18] ls /brokers/ids
[0]
```

4. Zookeeper presents information in a directory-like structure, with each node having 0 or more children listed with the ls command. Each node also has content that can be retrieved with a get command. To get the information for the Kafka broker, run this command

```get /brokers/ids/1```

Which will return data similar to this...

```
{"features":{},"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://192.168.1.14:9092"],"jmx_port":-1,"port":9092,"host":"192.168.1.14","version":5,"timestamp":"1724097127252"}
Same for after the topic is created.
```

Later on in this example, a topic will be created that can be viewed in Zookeeper by using:
```ls /brokers/topics```


## 3. Starting MySQL

Use this command to start MySQL or run the shell script.

```
docker run -it --rm --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=debezium -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw quay.io/debezium/example-mysql:2.7 --gtid_mode=ON --enforce-gtid-consistency=ON --server_id=1
```

Some notes:

MYSQL_ROOT_PASSWORD=debezium (sets root pass to Debezium)

 -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw (Adds a user and sets password)
 
 --gtid_mode=ON (Turns on Global Transaction IDs which help correlate which change(s) can be attributed to which transaction)

 --enforce-gtid-consistency=ON (enforces the use of GTIDs)

 --server_id=1 (sets server id)

 The binary log, which is used for replication and is enabled by default, is used by Debezium. 
 
 Note that it uses local host port 3306 and will conflict if another service is using that port.


## 4. Starting a MySQL CLI

```
docker run -it --rm --name mysqlterm --link mysql mysql:8.2 sh -c 'exec mysql -h"$MYSQL_PORT_3306_TCP_ADDR" -P"$MYSQL_PORT_3306_TCP_PORT" -uroot -p"$MYSQL_ENV_MYSQL_ROOT_PASSWORD"'
```

This command runs a MySQL command line client in the MySQL container. 

Having this available in a terminal is helpful if you do not have a MySQL client installed locally. 


### Check to see that the binlog is enabled

 ```select @@GLOBAL.log_bin;```

 ```
 
+------------------+
| @@GLOBAL.log_bin |
+------------------+
|                1 |
+------------------+

```


## 5. Start Kafka Connect

The following will start a Kafka Connect instance.

```
docker run -it --rm --name connect -p 8083:8083 -e GROUP_ID=1 -e CONFIG_STORAGE_TOPIC=my_connect_configs -e OFFSET_STORAGE_TOPIC=my_connect_offsets -e STATUS_STORAGE_TOPIC=my_connect_statuses --link kafka:kafka --link mysql:mysql quay.io/debezium/connect:2.7
```

Notes:

--link kafka:kafka --link mysql:mysql (allow this instance to see those instances)

This requires that port 8083 be available on the host.


### Verify Kafka Connect is running

```curl localhost:8083/ | jq```

Should return something like...

```
{
  "version": "3.7.0",
  "commit": "2ae524ed625438c5",
  "kafka_cluster_id": "R68-tchqQ4-H35YIKP8i8w"
}
```

Note that this requires the JSON command line parser tool jq be installed on your computer.

If jq is not installed, you can run:
```
curl localhost:8083/
```
The format will be all one string with no new lines.

### Verify that the Debezium MySQL connector is available in Kafka Connect

```curl localhost:8083/connector-plugins | jq```

Look for:

```
{
    "class": "io.debezium.connector.mysql.MySqlConnector",
    "type": "source",
    "version": "2.7.0.Final"
  },
```


## 6 Deploy connector

```
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d'{ "name": "inventory-connector", "config": { "connector.class": "io.debezium.connector.mysql.MySqlConnector", "tasks.max": "1", "database.hostname": "mysql", "database.port": "3306", "database.user": "debezium", "database.password": "dbz", "database.server.id": "184054", "topic.prefix": "dbserver1", "database.include.list": "inventory", "schema.history.internal.kafka.bootstrap.servers": "kafka:9092", "schema.history.internal.kafka.topic": "schemahistory.inventory" } }'
```

This command sets up the connector.
(make this a table)

"database.hostname": "mysql" = Connect to the host MySQL (the Docker container that was started in the previous command).

"database.port": "3306" = Connect to port 3306, the standard MySQL port.

"database.user": "debezium" = User to connect to MySQL.

"database.password": "dbz" = Password for the connection.

"database.server.id": "184054" = Debezium captures CDC data by identifying itself to MySQL as a MySQL server participating in a replication cluster, and therefore it needs to provide a server id.

"topic.prefix": "dbserver1" = Prefix to append to the Kafka topic.

"database.include.list": "inventory" = Specifies which database to replicate.


### Verify the connection has been configured 

```curl -H "Accept:application/json" localhost:8083/connectors/```

Should return:

```["inventory-connector"]```


## 7 Deploy a topic watcher

This command will display any new data in the Kafka topic.

If, for example, any table in the inventory database is modified, you will see that reflected in this terminal. 

```
docker run -it --rm --name watcher --link zookeeper:zookeeper --link kafka:kafka quay.io/debezium/kafka:2.7 watch-topic -a -k dbserver1.inventory.customers
```

This command will display to the terminal any changes in the Kafka topic used for our CDC/Debezium pipeline.


## Add a record to the inventory.customers table

Adding a record to the inventory.customers table should be reflected in the topic-watcher terminal.


### View the customers table

```
docker exec mysql mysql -umysqluser -pmysqlpw inventory -e "select * from customers"
```

You should see four rows.

Add a row

```
docker exec mysql mysql -umysqluser -pmysqlpw inventory -e 'insert into customers VALUES (NULL, "*********", "***********", "**************")'
```

Using ********* should make the entry into that wall of text easier to view.


## 8. Start Event Store DB

```
docker run -d --name "$container_name" -it -p 2113:2113 -p 1113:1113 \
     eventstore/eventstore:lts --insecure --run-projections=All \
     --enable-external-tcp --enable-atom-pub-over-http;
```


## Summary up to this point

mysql->binlog->debezium->kafka is now in place. 

What is needed is an application that reads the Kafka topic of Change Data Events from MySQL and writes those into EventStoreDB.

Sample code is available in the Python directory.

A quick summary of the code. 

1. Create a Kafka consumer
2. Create an EventStoreDB client
3. Iterate in a continuously running loop over Kafka output and write to Event Store

EventStoreDB manages data as immutable "events" written to an ordered log, where events are aggregated into streams. Events have the following attributes. 

Event Type: In our case, Event Type will be the SQL operation: Create, Update, Delete. 

Data: "The payload." In our case, this will be the key and value received from Debezim through Kafka and written as JSON.

MetaData: In our case, metadata will consist of the offset from Kafka, the timestamp, and the transaction ID of the SQL transaction that caused the change. This data is represented using JSON.

Stream_Name: In this example, one stream for each row in the tables will be monitored for changes. For example, an insert of row 1 into the table customers would lead to an event of Event Type: insert, into the stream customers-1.

If that row were updated, the stream customers-1 would have an update event appended to the stream. 

If that row were deleted, the stream customers-1 would have a delete event appended to the stream.

There is a separate section on Stream Design considerations and Event Store Features. 


## Stream Design Considerations and Features of Event Store

Add stuff on projections, Category Projections, and correlation ID projections.



