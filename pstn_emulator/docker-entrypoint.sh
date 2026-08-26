#!/bin/sh

set -e

# run as user asterisk by default
ASTERISK_USER=${ASTERISK_USER:-asterisk}
ASTERISK_GROUP=${ASTERISK_GROUP:-${ASTERISK_USER}}

if [ "$1" = "" ]; then
  COMMAND="/usr/sbin/asterisk -U ${ASTERISK_USER} -p -vvvf"
else
  COMMAND="$@"
fi

if [ "${ASTERISK_UID}" != "" ] && [ "${ASTERISK_GID}" != "" ]; then
  # recreate user and group for asterisk
  # if they've sent as env variables (i.e. to macth with host user to fix permissions for mounted folders

  deluser asterisk && \
  addgroup -g ${ASTERISK_GID} ${ASTERISK_GROUP} && \
  adduser -D -H -u ${ASTERISK_UID} -G ${ASTERISK_GROUP} ${ASTERISK_USER} \
  || exit
fi

chown -R ${ASTERISK_USER}: /var/log/asterisk \
                           /var/lib/asterisk \
                           /var/run/asterisk \
                           /var/spool/asterisk \
                           /etc/asterisk; \


if [ -n "$RTP_PORT_FROM" ]; then
  sed -i "s/10000/$RTP_PORT_FROM/g" /etc/asterisk/rtp.conf
fi

if [ -n "$RTP_PORT_TO" ]; then
  sed -i "s/10020/$RTP_PORT_TO/g" /etc/asterisk/rtp.conf
fi

if [ -n "$SIP_EXTERNAL_ADDR" ]; then
  sed -i "s/;external_media_address/external_media_address/g" /etc/asterisk/pjsip.conf
  sed -i "s/;external_signaling_address/external_signaling_address/g" /etc/asterisk/pjsip.conf
  sed -i "s/external_media_ipv4/$SIP_EXTERNAL_ADDR/g" /etc/asterisk/pjsip.conf
  sed -i "s/external_sip_ipv4/$SIP_EXTERNAL_ADDR/g" /etc/asterisk/pjsip.conf
fi

if [ -n "$SIP_EXTERNAL_PORT" ]; then
  sed -i "s/external_sip_port/$SIP_EXTERNAL_PORT/g" /etc/asterisk/pjsip.conf
  sed -i "s/;external_signaling_port/external_signaling_port/g" /etc/asterisk/pjsip.conf
fi

# PJSIP identify for the OML trunk via kamailio-pstn. El match es CIDR (sin DNS
# en el load de Asterisk): se inyecta identify/match=${SUBNET} bajo la línea
# remote_hosts del wizard [01177660010]. Así el identify no depende de que
# kamailio-pstn ya exista en el DNS de Docker al arrancar.
PSTN_PEER="${KAMAILIO_PSTN_HOSTNAME:-kamailio-pstn}"
WIZARD=/etc/asterisk/pjsip_wizard.conf
if [ -f "$WIZARD" ]; then
  if [ "$PSTN_PEER" != "kamailio-pstn" ]; then
    sed -i "s/kamailio-pstn/${PSTN_PEER}/g" "$WIZARD"
  fi
  if [ -n "$SUBNET" ] && ! grep -q "identify/match=${SUBNET}" "$WIZARD"; then
    sed -i "/^remote_hosts=${PSTN_PEER}\$/a identify/match=${SUBNET}" "$WIZARD"
  fi
fi

exec ${COMMAND}
