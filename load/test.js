// Open-model load test: requests arrive at a fixed RATE per second regardless of
// how fast the service answers, so queueing delay shows up in latency instead of
// silently lowering the offered load (as a closed VU loop would). See docs/decisions/002.
//
//   k6 run -e RATE=40 -e OUT=results/raw/rate40.json load/test.js
//   k6 run -e RATE=40 -e SERVICE=exponential load/test.js     # client-drawn Exp(MEAN) delays
//
// A warm-up scenario runs first at the same rate; only the "main" scenario is summarised
// (the thresholds below make k6 report the scenario:main sub-metrics).
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const RATE = parseFloat(__ENV.RATE || '10');
const DURATION = __ENV.DURATION || '60s';
const WARMUP = __ENV.WARMUP || '10s';
const SERVICE = __ENV.SERVICE || 'constant';        // constant | exponential
const MEAN = parseFloat(__ENV.MEAN || '0.05');      // mean delay asked of the server, seconds
const OUT = __ENV.OUT || `results/raw/rate${RATE}.json`;

// k6 rates are integers per timeUnit, so express the rate per minute for fractional values.
const PER_MINUTE = Math.round(RATE * 60);

function scenario(duration, startTime) {
  return {
    executor: 'constant-arrival-rate',
    rate: PER_MINUTE,
    timeUnit: '1m',
    duration,
    startTime,
    // Enough VUs that the client never becomes the bottleneck; k6 reports
    // dropped_iterations if it runs out.
    preAllocatedVUs: Math.max(10, Math.ceil(RATE)),
    maxVUs: Math.max(50, Math.ceil(RATE * 10)),
  };
}

export const options = {
  discardResponseBodies: true,
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    warmup: scenario(WARMUP, '0s'),
    main: scenario(DURATION, WARMUP),
  },
  thresholds: {
    'http_req_duration{scenario:main}': ['max>=0'],
    'http_reqs{scenario:main}': ['count>=0'],
    'http_req_failed{scenario:main}': ['rate>=0'],
    'dropped_iterations{scenario:main}': ['count>=0'],
  },
};

function delaySeconds() {
  if (SERVICE === 'exponential') {
    return Math.min(-MEAN * Math.log(1 - Math.random()), 10);   // httpbin caps /delay at 10 s
  }
  return MEAN;
}

export default function () {
  const res = http.get(`${BASE_URL}/delay/${delaySeconds().toFixed(4)}`, { timeout: '60s' });
  check(res, { 'status 200': (r) => r.status === 200 });
}

export function handleSummary(data) {
  const d = data.metrics['http_req_duration{scenario:main}'].values;
  const line = `rate=${RATE}/s ${SERVICE} p50=${d.med.toFixed(1)}ms p95=${d['p(95)'].toFixed(1)}ms -> ${OUT}\n`;
  return { [OUT]: JSON.stringify(data, null, 2), stdout: line };
}
