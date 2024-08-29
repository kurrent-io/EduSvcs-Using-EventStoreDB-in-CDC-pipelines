docker run -it --rm --name kafka -p 9092:9092 -e ADVERTISED_HOST_NAME=$(ipconfig getifaddr en0) --link zookeeper:zookeeper quay.io/debezium/kafka:2.7
