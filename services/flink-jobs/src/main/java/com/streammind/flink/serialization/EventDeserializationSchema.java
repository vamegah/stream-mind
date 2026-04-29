package com.streammind.flink.serialization;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import java.io.IOException;

public class EventDeserializationSchema implements DeserializationSchema<Event> {
    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public Event deserialize(byte[] message) throws IOException {
        return mapper.readValue(message, Event.class);
    }

    @Override
    public boolean isEndOfStream(Event nextElement) {
        return false;
    }

    @Override
    public TypeInformation<Event> getProducedType() {
        return TypeInformation.of(Event.class);
    }
}