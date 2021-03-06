#!/bin/sh
# from http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/

### BEGIN INIT INFO
# Provides:          sudoChat server
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Web socket server for sudoChat messaging app
# Description:       Server for hosting chatrooms used by sudoChat client application
### END INIT INFO

DIR=/home/esyywar/sudoChat
DAEMON=$DIR/server.py
DAEMON_NAME=sudochat_server

DAEMON_USER=root

PIDFILE=/tmp/$DAEMON_NAME.pid

. /lib/lsb/init-functions

# Start command:
# start-stop-daemon --start --startas /home/esyywar/sudoChat/server.py --user root --background --pidfile /tmp/sudochat_server --make-pidfile

do_start () {
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon -–start –-startas $DAEMON -–user $DAEMON_USER -–background –-pidfile $PIDFILE –-make-pidfile 
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon -–stop –-pidfile $PIDFILE –-retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0