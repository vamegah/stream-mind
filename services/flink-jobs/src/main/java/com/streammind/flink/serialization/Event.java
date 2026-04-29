package com.streammind.flink.serialization;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;

public class Event implements Serializable {
    @JsonProperty("event_id")
    public String eventId;
    @JsonProperty("event_type")
    public String eventType;
    @JsonProperty("user_id_token")
    public String userIdToken;
    @JsonProperty("content_id")
    public String contentId;
    @JsonProperty("timestamp_ms")
    public long timestampMs;
    @JsonProperty("region")
    public String region;
    @JsonProperty("device_type")
    public String deviceType;
}