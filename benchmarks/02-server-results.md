# 02 — Server Load Test Results

## 10-user load test
- Total RPS: 0.60
- P50 latency: 14,000 ms
- P95 latency: 18,000 ms
- P99 latency: 18,000 ms
- Failures: 0
- Total requests: 37

## 50-user load test
- Total RPS: 0.56
- P50 latency: 23,000 ms
- P95 latency: 35,000 ms
- P99 latency: 37,000 ms
- Failures: 0
- Total requests: 28

## /metrics recording
- Captured 60 seconds of `http://localhost:8080/metrics` to `benchmarks/02-server-metrics.csv`.
- Recorded 35 samples from the running server.
- Observed `llamacpp:kv_cache_usage_ratio = 0.0` in the metrics output, which indicates this server exposure did not report a non-zero KV-cache ratio for this model path.
- Peak concurrent `llamacpp:requests_processing` was 51 while the server handled 50 locust users.
