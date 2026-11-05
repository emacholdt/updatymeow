#!/usr/bin/env bash
set -e

PREFIX="${HOME}/.local"
echo "==> Uninstalling UpdatyMeow..."

rm -f "${PREFIX}/bin/updatymeow"
rm -f "${PREFIX}/share/applications/updatymeow.desktop"
rm -f "${PREFIX}/share/icons/hicolor/"*/apps/updatymeow.png "${PREFIX}/share/icons/hicolor/scalable/apps/updatymeow.svg"
rm -rf "${PREFIX}/lib/updatymeow"
rm -f "${HOME}/.config/autostart/updatymeow.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${PREFIX}/share/applications" >/dev/null 2>&1 || true
fi

echo "✓ UpdatyMeow uninstalled."
