FROM alpine:latest
ENV LANG en_US.utf8

RUN apk update \
    && apk add sngrep asterisk openrc openntpd sipp
COPY conf/*.conf /etc/asterisk/
COPY interfaces /etc/network/
COPY audios/* /var/lib/asterisk/sounds/

EXPOSE 6060/udp 10000-10020/udp
CMD ["/usr/sbin/asterisk", "-cvvv"]
