#!/bin/bash
NAME="VoiceToAI"
COMMAND="/usr/bin/python3 /media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/voice_to_ai_clipboard.py"
BINDING="<Control><Alt>v"

# Find an available slot
i=0
while gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/ name > /dev/null 2>&1; do
    i=$((i+1))
done

NEW_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom$i/"

# Add to the list
CURRENT=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)
if [[ "$CURRENT" == "[]" ]]; then
    NEW_LIST="['$NEW_PATH']"
else
    NEW_LIST="${CURRENT%]*}, '$NEW_PATH']"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_LIST"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$NEW_PATH name "$NAME"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$NEW_PATH command "$COMMAND"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$NEW_PATH binding "$BINDING"
