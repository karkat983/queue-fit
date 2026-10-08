# httpbin (open source, https://github.com/psf/httpbin) served by gunicorn sync workers.
# Built locally so it runs natively on arm64 and amd64 with pinned versions.
FROM python:3.12-slim
RUN pip install --no-cache-dir "httpbin==0.10.2" "gunicorn==23.0.0"
EXPOSE 80
# A sync worker serves one request at a time, so WORKERS is the true server count c.
CMD ["sh", "-c", "exec gunicorn -b 0.0.0.0:80 -w ${WORKERS:-4} -k sync httpbin:app"]
