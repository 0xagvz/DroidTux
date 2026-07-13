#!/bin/bash
# Log execution
exec &> >(logger -t droidtux-trigger)
echo "Trigger called with argument: $1"

# Find active sessions and launch user systemd service
for uid in $(loginctl list-sessions --no-legend | awk '{print $2}'); do
    user=$(id -un "$uid")
    echo "Processing session for user: $user (UID: $uid)"
    
    # Better way to find DISPLAY
    display=$(sudo -u "$user" env | grep '^DISPLAY=' | cut -d= -f2-)
    if [ -z "$display" ]; then
        display=$(pgrep -u "$uid" -a gnome-session | grep -o 'DISPLAY=[^ ]*' | cut -d= -f2 | head -n1)
        [ -z "$display" ] && display=$(pgrep -u "$uid" -a x-session-manager | grep -o 'DISPLAY=[^ ]*' | cut -d= -f2 | head -n1)
        [ -z "$display" ] && display=":0"
    fi
    echo "Found DISPLAY: $display"

    if [ "$1" == "add" ]; then
        echo "Restarting service for $user..."
        sudo -u "$user" env DISPLAY="$display" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user restart android-integrator.service
    elif [ "$1" == "remove" ]; then
        echo "Stopping service for $user..."
        sudo -u "$user" env XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user stop android-integrator.service
    fi
done
