#!/usr/bin/env bash
set -e

# Default to user install (~/.local)
PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
APP_DIR="${PREFIX}/share/applications"
LIB_DIR="${PREFIX}/lib/updatymeow"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing UpdatyMeow to ${PREFIX}..."

mkdir -p "${BIN_DIR}" "${APP_DIR}" "${LIB_DIR}"

if [ "$1" == "--dev" ] || [ "$1" == "--link" ]; then
    echo "Creating developer symlinks..."
    ln -sf "${SCRIPT_DIR}/run.py" "${BIN_DIR}/updatymeow"
else
    # Copy files
    cp -r "${SCRIPT_DIR}/updatymeow" "${LIB_DIR}/"
    cp "${SCRIPT_DIR}/run.py" "${LIB_DIR}/"
    cat << 'EOF' > "${BIN_DIR}/updatymeow"
#!/usr/bin/env bash
exec python3 "${HOME}/.local/lib/updatymeow/run.py" "$@"
EOF
    chmod +x "${BIN_DIR}/updatymeow"
fi

# Install desktop entry
cp "${SCRIPT_DIR}/updatymeow.desktop" "${APP_DIR}/updatymeow.desktop"
chmod +x "${APP_DIR}/updatymeow.desktop"

# Refresh desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" >/dev/null 2>&1 || true
fi

echo "✓ UpdatyMeow successfully installed!"
echo "  Binary: ${BIN_DIR}/updatymeow"
echo "  Desktop: ${APP_DIR}/updatymeow.desktop"
echo "You can now run 'updatymeow' from anywhere or launch it from your application menu."
