FROM alpine:latest
ENV LANG en_US.utf8

RUN apk update \
    && apk add sngrep asterisk openrc openntpd sipp
RUN mkdir /etc/asterisk/custom

COPY docker-entrypoint.sh /
COPY conf/*.conf /etc/asterisk/
COPY interfaces /etc/network/
COPY audios/* /var/lib/asterisk/sounds/

EXPOSE 5060/udp
EXPOSE 4569/udp

ENTRYPOINT ["/docker-entrypoint.sh"]
