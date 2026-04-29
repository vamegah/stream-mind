CREATE KEYSPACE IF NOT EXISTS streammind WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS streammind.minute_trending (
    content_id text,
    date_hour text,
    window_end timestamp,
    play_count bigint,
    PRIMARY KEY ((content_id, date_hour), window_end)
) WITH CLUSTERING ORDER BY (window_end DESC);


CREATE TABLE streammind.privacy_audit (
    user_token text,
    query_time timestamp,
    endpoint text,
    budget_consumed double,
    remaining double,
    PRIMARY KEY ((user_token), query_time)
);