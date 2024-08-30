# Change Data Capture (CDC) to Event Store Example using Debezium

This directory has scripts that will launch docker instances to enable a MySQL to EventStoreDB CDC pipeline.


## How this project is structured

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

## Let's get started

--------------

## 1. Starting Zookeeper

Kafka depends on Zookeeper, so before we start kafka zookeeper needs to be available. 

Note that recently the zookeeper requirement is no longer needed, and kafka can using raft, called kraft instead of zookeeper. This project has yet to migrate to a kraft enabled kafka.

### What is Zookeeper?

A Zookeeper cluster provides a distributed, consistent, fault-tolerant directory or tree of information. Typical use cases for Zookeeper are configuration management, leader election, message queues, and notification systems.

### What products use Zookeeper?

The valuable service provided by Zookeeper underpins many projects, with Hadoop and Kafka being the more widely used examples. A project built on top of Zookeeper, called Bookeeper is used by Apache Pulsar.

### How does Kafka use Zookeeper?

Kafka uses Zookeeper to track which nodes are available, what topics are being served, etc.

Kafka requires and uses Zookeeper as a core requirement of providing the Kafka service.

### Will you need to interact directly with Zookeeper for this demo?

No.

In this example, you don't need to interact directly with Zookeeper, but Kafka requires it, so it is the first service you will need to start.

However, in the interest of learning how each part of the system works, the Zookeeper instance is started with some useful settings, enabling 4letterwords, that can be useful if you want to verify a working Zookeeper quorum.

The start command to start a Docker instance is below. Note the setting 

``` -e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*" ```
This setting enables 4letterwords.

You pass ZK "ruok" for "Are You Okay" over telnet, and if Zookeeper is running, it will return "imok" for "I am okay."

Here is the command.

```
docker run -e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*" -it --rm --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 quay.io/debezium/zookeeper:2.7
```

### Shell script alternative to cut and paste

Since copying and pasting commands can sometimes lead to accidental introduction of newlines, or other characters, a shell script is provided as part of this repo. Instead of Copy/Paste you can clone this repo locally and run

```sh 01_zookeper.sh```

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

### If you have issues

This command works with this version of Zookeeper and the specified Docker container.

If you want to use another version of Zookeeper or another Docker container, you may need to change this "-e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*"". This is one way to turn on the 4letter words functionality. You probably do not require 4letter words, but they are used here to validate that Zookeeper is working.

--------------

## 2. Starting Kafka

You can start Kafka with the following command.

```
docker run -it --rm --name kafka -p 9092:9092 -e ADVERTISED_HOST_NAME=<YOUR_HOSTNAME_OR_IP_ADDRESS> --link zookeeper:zookeeper quay.io/debezium/kafka:2.7
```

Points to note...

Kafka needs to know your laptop's hostname for the Python application to connect to it. The other Docker instances are on the same Docker network due to the —-link setting when the containers are started.  The Python example is not within a docker container, and will require code running on your laptop to connect to kafka. Setting the advertised host name is one way to enable that connection.

The shell script uses the value returned from the command. 
```
ipconfig getifaddr en0
```

If that command does not work on your computer, edit either the shell script, or the command to copy and paste so that it includes your IP address.

You can test the command below in a terminal if you have issues.This code works on mac, and probably on linux, windows users will have to edit the command.

```
echo ADVERTISED_HOST_NAME=$(ipconfig getifaddr en0)
ADVERTISED_HOST_NAME=192.168.1.14
```

### Ports used by Kafka

Note that Kafka uses port 9092 and will fail if that port is not available.

### Kafka must be able to connect to Zookeeper

The ```--link zookeeper:zookeeper``` allows this container to see the Zookeeper container as if they were on the same network.

### Optional: Verify Kafka has registered with Zookeeper

The Zookeeper container will have an instance of the Zookeeper Command Line Client (zkCli.sh)

If you want to explore and verify that Kafka has found Zookeeper, you can run the following commands.

#### A. Connect to the instance

```docker exec -it zookeeper sh```

#### B. Launch the zkCli

 ```/zookeeper/bin/zkCli.sh```

#### C. List the Kafka broker's ids

```ls /brokers/ids```

returns
```[1]```

This shows that Kafka is connected and registered with ZK quorum.

If you stopped Kafka you would  see the list of broker ids go to 0

```
[zk: localhost:2181(CONNECTED) 18] ls /brokers/ids
[0]
```

#### D. Get the data for broker node from Zookeeper 

Zookeeper presents information in a directory-like structure, with each node having 0 or more children that can be listed with the ls command. Each node also has content that can be retrieved with a get command. To get the information for the Kafka broker, run this command.

```get /brokers/ids/1```

Which will return data similar to this...

```
{"features":{},"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://192.168.1.14:9092"],"jmx_port":-1,"port":9092,"host":"192.168.1.14","version":5,"timestamp":"1724097127252"}
Same for after the topic is created.
```

Later on in this example, a topic will be created that can be viewed in Zookeeper by using:
```ls /brokers/topics```

--------------

## 3. Starting MySQL

Use this command to start MySQL or run the shell script, ```sh 03_mysql.sh```

```
docker run -it --rm --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=debezium -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw quay.io/debezium/example-mysql:2.7 --gtid_mode=ON --enforce-gtid-consistency=ON --server_id=1
```

Some notes on the command parameters:

'''-e MYSQL_ROOT_PASSWORD=debezium''' (sets root pass to Debezium)

'''-e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw''' (Adds a user and sets password)
 
'''--gtid_mode=ON''' (Turns on Global Transaction IDs which help correlate which change(s) can be attributed to which transaction)

'''--enforce-gtid-consistency=ON''' (enforces the use of GTIDs)

'''--server_id=1''' (sets server id) all participants in replication, and debezium impersonates a replication node, must have unique server-id values. 

Just a note that the binary log, which is used for replication and is enabled by default, is used by Debezium.

### Ports required for MySQL

Note that MySQL uses local host port 3306 and will fail to start if another service is using that port.

--------------

## 4. Starting a MySQL CLI

This command will start a MySQL command line session attached to the MySQL server started earlier. This is not technically required by the demo, but can be useful if you want to explore. From this prompt you can switch to the inventory database and run SQL commands against the tables that are part of our CDC pipeline.

```docker run -it --rm --name mysqlterm --link mysql mysql:8.2 sh -c 'exec mysql -h"$MYSQL_PORT_3306_TCP_ADDR" -P"$MYSQL_PORT_3306_TCP_PORT" -uroot -p"$MYSQL_ENV_MYSQL_ROOT_PASSWORD"'
```

Having this available in a terminal is particularly helpful if you do not have a MySQL client installed locally. Note if you do want to connect from the terminal on your laptop to the MySQL in the docker container you will have to specify -h127.0.0.1, otherwise the connection will think the server is local and try the socket, instead of the network port.

### Verify that the binlog is enabled

This command is informational only, the docker container provided will run MySQL with the binlog enabled. It is also enabled by default, but it is worth checking, or making it part of your debug routine if things go wrong. 

 ```select @@GLOBAL.log_bin;```

 ```
 
+------------------+
| @@GLOBAL.log_bin |
+------------------+
|                1 |
+------------------+

```

--------------

## 5. Start Kafka Connect

The following will start a Kafka Connect instance. Or you can run the shell script, ```sh 05_kafka_connect.sh```

```
docker run -it --rm --name connect -p 8083:8083 -e GROUP_ID=1 -e CONFIG_STORAGE_TOPIC=my_connect_configs -e OFFSET_STORAGE_TOPIC=my_connect_offsets -e STATUS_STORAGE_TOPIC=my_connect_statuses --link kafka:kafka --link mysql:mysql quay.io/debezium/connect:2.7
```

### Command details

```--link kafka:kafka --link mysql:mysql``` (allow this instance to see those instances)

### Ports required by Kafka

In order to run this docker container port 8083 must be available on the host.

### Verify Kafka Connect is running

This curl command can be used to verify that Kafka Connect is running.


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
The format will be all one string with no new lines, but it will still show that Kafka Connect is functioning.

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

--------------

## 6. Deploy connector

Once again, you can copy this command and paste into a terminal, or you can run the shell script ```sh 06_deploy_connector.sh```


```
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d'{ "name": "inventory-connector", "config": { "connector.class": "io.debezium.connector.mysql.MySqlConnector", "tasks.max": "1", "database.hostname": "mysql", "database.port": "3306", "database.user": "debezium", "database.password": "dbz", "database.server.id": "184054", "topic.prefix": "dbserver1", "database.include.list": "inventory", "schema.history.internal.kafka.bootstrap.servers": "kafka:9092", "schema.history.internal.kafka.topic": "schemahistory.inventory" } }'
```

This command sets up the connector.

### Settings details

"database.hostname": "mysql" = Connect to the host MySQL (the Docker container that was started in the previous command)

"database.port": "3306" = Connect to port 3306, the standard MySQL port

"database.user": "debezium" = User to connect to MySQL

"database.password": "dbz" = Password for the connection

"database.server.id": "184054" = Debezium captures CDC data by identifying itself to MySQL as a MySQL server participating in a replication cluster, and therefore it needs to provide a server id

"topic.prefix": "dbserver1" = Prefix to append to the Kafka topic

"database.include.list": "inventory" = Specifies which database to replicate

### Verify the connection has been configured 

```curl -H "Accept:application/json" localhost:8083/connectors/```

Should return:

```["inventory-connector"]```

--------------

## 7 Deploy a topic watcher

This command will display any new data in the Kafka topic to the terminal. 

If, for example, any table in the inventory database is modified, you will see that reflected in this terminal.

The command is below, or you can run the shell script ```sh 07_topic_watcher.sh```

```
docker run -it --rm --name watcher --link zookeeper:zookeeper --link kafka:kafka quay.io/debezium/kafka:2.7 watch-topic -a -k dbserver1.inventory.customers
```

This command will display to the terminal any changes in the Kafka topic used for our CDC/Debezium pipeline.

### Add a record to the inventory.customers table to verify functioning pipeline

Adding a record to the inventory.customers table should be reflected in the topic-watcher terminal.

The commands below will demonstrate.

### View the customers table

```
docker exec mysql mysql -umysqluser -pmysqlpw inventory -e "select * from customers"
```

You should see four rows.

### Add a row

```
docker exec mysql mysql -umysqluser -pmysqlpw inventory -e 'insert into customers VALUES (NULL, "*********", "***********", "**************")'
```

Using ********* should make the entry into that wall of text that is displayed in the topic watcher termina,  easier to scan to detect the change.

--------------

## 8. Start Event Store DB

```
docker run -d --name "$container_name" -it -p 2113:2113 -p 1113:1113 \
     eventstore/eventstore:lts --insecure --run-projections=All \
     --enable-external-tcp --enable-atom-pub-over-http;
```

Note that this starts EventStoreDB and you can verify by pointing a browser at http://localhost:2113

Check projections and make sure they are running. 

--------------

## Summary up to this point

mysql->binlog->debezium->kafka is now in place. 

What is needed is an application that reads the Kafka topic of Change Data Events from MySQL and writes those into EventStoreDB.

Sample code is available in the Python directory. The k_to_es_stream_per_row.py program is the code that reads messages off the kafka topic, and transforms them into events in EventStoreDB.

A quick summary of the code.

1. Create a Kafka consumer
2. Create an EventStoreDB client
3. Iterate in a continuously running loop over Kafka output and write to Event Store

EventStoreDB manages data as immutable "events" written to an ordered log, where events are aggregated into streams. Events have the following attributes.


* Event Type: 

In our case, Event Type will be the SQL operation: Create, Update, Delete. 

* Data: 

The payload of the Kafka message is the basis for the Event Data. In our case, this will be the key and value received from Debezium through Kafka and written as JSON.

* Event MetaData:

In our case, metadata will consist of the offset from Kafka, the timestamp, and the transaction ID of the SQL transaction that caused the change. This data is represented using JSON.

* Stream_Name: 

In this example, one stream for each row in the tables will be created and appended to. 

For example, an insert of row 1 into the table customers would lead to an event of Event Type: insert, into the stream customers-1.

If that same row, row1, were updated, the stream customers-1 would have an update event appended to the stream customers-1.

If that row were deleted, the stream customers-1 would have a delete event appended to it.

See the Readme in the top level directory for Stream Design considerations and related Event Store Features.

--------------