FROM alpine:latest
ENV LANG en_US.utf8

RUN apk update \
    && apk add sngrep asterisk openrc openntpd sipp python3 py3-pip
RUN mkdir /etc/asterisk/custom
RUN pip3 install --no-cache-dir --break-system-packages pyst2==0.5.1 requests

COPY docker-entrypoint.sh /
COPY conf/*.conf /etc/asterisk/
COPY interfaces /etc/network/
COPY audios/silence/* /var/lib/asterisk/sounds/silence/
COPY audios/* /var/lib/asterisk/sounds/
COPY agi/*.py /var/lib/asterisk/agi-bin/

EXPOSE 5060/udp
EXPOSE 4569/udp

ENTRYPOINT ["/docker-entrypoint.sh"]
