package com.streammind.flink;

import com.streammind.flink.serialization.Event;
import com.streammind.flink.serialization.EventDeserializationSchema;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.typeinfo.Types;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.streaming.api.windowing.assigners.SlidingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;

public class AnomalyDetectionJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

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

        // Filter plays
        DataStream<Event> plays = events.filter(e -> e.eventType.equals("play"));

        // Key by content_id, count per minute using a sliding window of 1 min every 1 min (simplified: use tumbling window)
        // Then detect drop by comparing current minute count with average of last 5 minutes.
        // Better: use a ProcessFunction that accumulates counts per minute.
        // We'll implement a simplified version: count per minute using tumbling window, then detect drop.
        DataStream<Event> perMinuteCounts = plays
                .keyBy(e -> e.contentId)
                .window(TumblingEventTimeWindows.of(Time.minutes(1)))
                .process(new CountPerWindowFunction()); // custom function to output (contentId, count, windowEnd)

        // Detect anomaly
        perMinuteCounts
                .keyBy(t -> t.contentId)
                .process(new AnomalyDetectionFunction())
                .addSink(createAnomalyKafkaSink());

        env.execute("Anomaly Detection Job");
    }

    // Helper to emit (contentId, count, windowEnd)
    private static class CountPerWindowFunction extends org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction<Event, String, String, TimeWindow> {
        @Override
        public void process(String key, Context context, Iterable<Event> elements, Collector<String> out) {
            long count = elements.spliterator().getExactSizeIfKnown();
            String anomalyEvent = String.format("{\"content_id\":\"%s\",\"count\":%d,\"window_end\":%d}", key, count, context.window().getEnd());
            out.collect(anomalyEvent);
        }
    }

    private static class AnomalyDetectionFunction extends KeyedProcessFunction<String, String, String> {
        private transient ValueState<Deque<Long>> historyState; // store counts for last 5 minutes
        private static final int WINDOW_SIZE = 5;

        @Override
        public void open(Configuration parameters) {
            ValueStateDescriptor<Deque<Long>> descriptor = new ValueStateDescriptor<>("history", Types.GENERIC(Deque.class));
            historyState = getRuntimeContext().getState(descriptor);
        }

        @Override
        public void processElement(String value, Context ctx, Collector<String> out) throws Exception {
            // Parse JSON: extract count
            String[] parts = value.split(",");
            long count = Long.parseLong(parts[1].split(":")[1].trim());
            Deque<Long> history = historyState.value();
            if (history == null) history = new ArrayDeque<>();
            history.addLast(count);
            if (history.size() > WINDOW_SIZE) history.removeFirst();
            historyState.update(history);

            if (history.size() == WINDOW_SIZE) {
                double avg = history.stream().mapToLong(Long::longValue).average().orElse(1.0);
                if (count < avg * 0.4) { // 60% drop
                    String anomaly = String.format("{\"anomaly_id\":\"%s\",\"content_id\":\"%s\",\"drop_percent\":%.1f,\"window_end\":%s}",
                            java.util.UUID.randomUUID(), parts[0].split(":")[1], (1 - count/avg)*100, parts[2].split(":")[1]);
                    out.collect(anomaly);
                }
            }
        }
    }

    private static org.apache.flink.streaming.api.functions.sink.SinkFunction<String> createAnomalyKafkaSink() {
        // Simplified: use Kafka sink. For brevity, we'll print to stdout for testing.
        // In production use FlinkKafkaProducer.
        return new org.apache.flink.streaming.api.functions.sink.PrintSinkFunction<>();
    }
}