FROM alpine:latest

RUN apk update

RUN apk add python3 && \
    apk add py3-yaml && \
    apk add py3-requests

COPY server.py /server.py
COPY discover_agent.py /discover_agent.py
COPY device.py /device.py

CMD ["python3", "server.py"]
