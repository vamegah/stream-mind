package com.streammind.flink;

import com.streammind.flink.serialization.Event;
import com.streammind.flink.serialization.EventDeserializationSchema;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.connectors.cassandra.CassandraSink;
import org.apache.flink.streaming.connectors.redis.RedisSink;
import org.apache.flink.streaming.connectors.redis.common.config.FlinkJedisPoolConfig;
import org.apache.flink.streaming.connectors.redis.common.mapper.RedisCommand;
import org.apache.flink.streaming.connectors.redis.common.mapper.RedisCommandDescription;
import org.apache.flink.streaming.connectors.redis.common.mapper.RedisMapper;
import java.time.Duration;

public class TrendingAggregationJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60000); // checkpoint every 1 minute

        // Kafka source
        KafkaSource<Event> source = KafkaSource.<Event>builder()
                .setBootstrapServers("kafka:9092")
                .setTopics("raw-events")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new EventDeserializationSchema())
                .build();

        DataStream<Event> events = env.fromSource(source, 
                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner((event, ts) -> event.timestampMs),
                "Kafka Source");

        // Filter only 'play' events
        DataStream<Event> plays = events.filter(e -> e.eventType.equals("play"));

        // Key by content_id, window 1 minute, count
        DataStream<Tuple2<String, Long>> trending = plays
                .map(new MapFunction<Event, Tuple2<String, Long>>() {
                    @Override
                    public Tuple2<String, Long> map(Event e) {
                        return Tuple2.of(e.contentId, 1L);
                    }
                })
                .keyBy(t -> t.f0)
                .window(TumblingEventTimeWindows.of(Time.minutes(1)))
                .sum(1);

        // 1. Cassandra sink
        CassandraSink.addSink(trending)
                .setQuery("INSERT INTO streammind.minute_trending (content_id, date_hour, window_end, play_count) VALUES (?, ?, ?, ?)")
                .setHost("cassandra", 9042)
                .build();

        // 2. Redis sink (write to sorted set 'trending:minute')
        FlinkJedisPoolConfig redisConfig = new FlinkJedisPoolConfig.Builder()
                .setHost("redis")
                .setPort(6379)
                .build();

        trending.addSink(new RedisSink<>(redisConfig, new RedisMapper<Tuple2<String, Long>>() {
            @Override
            public RedisCommandDescription getCommandDescription() {
                // Use ZADD to add/update score (play count) in sorted set
                return new RedisCommandDescription(RedisCommand.ZADD, "trending:minute");
            }
            @Override
            public String getKeyFromData(Tuple2<String, Long> data) {
                return data.f0;
            }
            @Override
            public String getValueFromData(Tuple2<String, Long> data) {
                return String.valueOf(data.f1);
            }
        }));

        env.execute("Trending Aggregation Job");
    }
}