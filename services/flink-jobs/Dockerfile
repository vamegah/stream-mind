FROM flink:1.18.1-scala_2.12-java11

# Copy uber jar
COPY target/flink-jobs-1.0-SNAPSHOT.jar /opt/flink/usrlib/flink-jobs.jar

# Copy job script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]