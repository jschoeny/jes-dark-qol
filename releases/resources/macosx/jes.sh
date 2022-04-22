#!/bin/sh
# Launches JES in place on Mac and Linux.

# Where are we?

#JES_BASE="$(dirname $(readlink -f $0))"
#JES_BASE="$( cd "$(dirname "$0")" ; pwd -P )"
APP_BASE="$(dirname "${BASH_SOURCE[0]}")/JES.app/Contents"
JES_BASE="$APP_BASE/Resources/Java"
JES_HOME="$JES_BASE/jes"
ICON_FILE="$APP_BASE/Resources/JESi2.icns"

if [ ! -x "$APP_BASE" ]; then
    # display error message with applescript
    osascript -e "tell application \"System Events\" to display dialog \"Could not find JES.app! Keep this script in the same directory as JES.app\" with title \"JES\" buttons {\"OK\"} default button 1"

    # exit with error
    exit 1
fi


# See if there's a user configuration file...

if test -d "$HOME/Library/Application Support"; then
    JESCONFIGDIR="$HOME/Library/Application Support/JES"
    JES_USER_PLUGINS="$HOME/Library/Application Support/JES/Plugins"
else
    JESCONFIGDIR="${XDG_CONFIG_HOME:-$HOME/.config}/jes"
    JES_USER_PLUGINS="${XDG_DATA_HOME:-$HOME/.local/share}/jes/plugins"
fi

if test -f "$JESCONFIGDIR/JESEnvironment.sh"; then
    source "$JESCONFIGDIR/JESEnvironment.sh"
fi



# What Java should we use?

# if ! test -z "$JES_JAVA_HOME"; then
#     JAVA="$JES_JAVA_HOME/bin/java"
# elif ! test -z "$JAVA_HOME"; then
#     JAVA="$JAVA_HOME/bin/java"
# else
#     JAVA=java
# fi
JAVA="/Library/Java/JavaVirtualMachines/jdk1.8.0_321.jdk/Contents/Home/bin/java"

# ...Did we find one?

if [ ! -x "$JAVA" ]; then
    # display error message with applescript
    osascript -e "tell application \"System Events\" to display dialog \"Error launching JES!\n\nYou need to have Java 8 (jdk1.8.0_321) installed on your Mac!\nVisit http://java.com for more information.\" with title \"${CFBundleName}\" buttons {\"OK\"} default button 1 with icon path to resource \"${CFBundleIconFile}\" in bundle (path to me)"

    # exit with error
    exit 1
fi

# Where's our Java code?

JARS="$JES_BASE/dependencies/jars"

CLASSPATH="$JES_HOME/classes.jar"

for jar in "$JARS"/*.jar; do
    CLASSPATH="$CLASSPATH:$jar"
done


# Where's our Python code?

PYTHONHOME="$JES_BASE/dependencies/jython"

PYTHONPATH="$JES_HOME/python:$JES_BASE/dependencies/python"


# Do we have any plugins to load?
# User plugins:

if test -d "$JES_USER_PLUGINS"; then
    for jar in "$JES_USER_PLUGINS"/*.jar; do
        CLASSPATH="$CLASSPATH:$jar"
    done
fi

# System plugins:

JES_SYSTEM_PLUGINS="$JES_BASE/plugins"

if test -d "$JES_SYSTEM_PLUGINS"; then
    for jar in "$JES_SYSTEM_PLUGINS"/*.jar; do
        CLASSPATH="$CLASSPATH:$jar"
    done
fi

# Built-in plugins:

JES_BUILTIN_PLUGINS="$JES_HOME/builtin-plugins"

if test -d "$JES_BUILTIN_PLUGINS"; then
    for jar in "$JES_BUILTIN_PLUGINS"/*.jar; do
        CLASSPATH="$CLASSPATH:$jar"
    done
fi


# Where should the Jython cache live?

if test -d "$HOME/Library/Caches"; then
    PYTHONCACHE="$HOME/Library/Caches/JES/jython-cache"
else
    PYTHONCACHE="${XDG_CACHE_HOME:-$HOME/.cache}/jes/jython-cache"
fi

mkdir -p $PYTHONCACHE


# What about JESConfig.properties?

JESCONFIG=$JESCONFIGDIR/JESConfig.properties

mkdir -p "$JESCONFIGDIR"


# All right, time to actually run it!

exec "$JAVA" \
    -classpath "$CLASSPATH" \
    -Xdock:icon="$ICON_FILE" \
    -Xdock:name="JES" \
    -Dfile.encoding="UTF-8" \
    -Djes.home="$JES_HOME" \
    -Djes.configfile="$JESCONFIG" \
    -Djes.plugins.user="$JES_USER_PLUGINS" \
    -Djes.plugins.system="$JES_SYSTEM_PLUGINS" \
    -Djes.plugins.builtin="$JES_BUILTIN_PLUGINS" \
    -Dpython.home="$PYTHONHOME" \
    -Dpython.path="$PYTHONPATH" \
    -Dpython.cachedir="$PYTHONCACHE" \
    -Dapple.laf.useScreenMenuBar=true \
    -Dapple.awt.application.appearance=system \
    ${JES_JAVA_MEMORY:--Xmx1024m} ${JES_JAVA_OPTIONS} \
    JESstartup "$@"
