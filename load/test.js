// Open-model load test: requests arrive at a fixed RATE per second regardless of
// how fast the service answers, so queueing delay shows up in latency instead of
// silently lowering the offered load (as a closed VU loop would).
//
//   k6 run -e RATE=40 -e OUT=results/raw/rate40.json load/test.js
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const ENDPOINT = __ENV.ENDPOINT || '/delay/0.05';
const RATE = parseInt(__ENV.RATE || '10', 10);
const DURATION = __ENV.DURATION || '60s';
const OUT = __ENV.OUT || `results/raw/rate${RATE}.json`;

export const options = {
  discardResponseBodies: true,
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    open_model: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      // Enough VUs that the client never becomes the bottleneck; k6 reports
      // dropped_iterations if it runs out.
      preAllocatedVUs: Math.max(10, RATE),
      maxVUs: Math.max(50, RATE * 10),
    },
  },
};

export default function () {
  const res = http.get(`${BASE_URL}${ENDPOINT}`, { timeout: '30s' });
  check(res, { 'status 200': (r) => r.status === 200 });
}

export function handleSummary(data) {
  const d = data.metrics.http_req_duration.values;
  const line = `rate=${RATE}/s p50=${d.med.toFixed(1)}ms p95=${d['p(95)'].toFixed(1)}ms -> ${OUT}\n`;
  return { [OUT]: JSON.stringify(data, null, 2), stdout: line };
}
