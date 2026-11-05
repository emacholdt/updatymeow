#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 1. Detect Version
VERSION="$(python3 -c "import updatymeow; print(updatymeow.__version__)")"
echo "==> Building self-contained AppImage for UpdatyMeow v${VERSION}..."

BUILD_DIR="${SCRIPT_DIR}/build"
DIST_DIR="${SCRIPT_DIR}/dist"
APPDIR="${BUILD_DIR}/UpdatyMeow.AppDir"
VENV_DIR="${BUILD_DIR}/build_venv"
APPIMAGETOOL="${BUILD_DIR}/appimagetool"

mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

# 2. Setup build virtualenv if needed
if [ ! -f "${VENV_DIR}/bin/pyinstaller" ]; then
    echo "==> Preparing build environment with PyInstaller & PyQt5..."
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install pyinstaller PyQt5
fi

# 3. Download appimagetool if not present
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "==> Downloading appimagetool..."
    curl -sL https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage -o "${APPIMAGETOOL}"
    chmod +x "${APPIMAGETOOL}"
fi

# 4. Clean previous AppDir
rm -rf "${APPDIR}" "${BUILD_DIR}/pyinstaller_build" "${BUILD_DIR}/pyinstaller_dist"

# 5. Run PyInstaller to bundle Python + PyQt5 + UpdatyMeow
echo "==> Bundling application with PyInstaller..."
"${VENV_DIR}/bin/pyinstaller" \
    --name updatymeow \
    --noconfirm \
    --windowed \
    --onedir \
    --distpath "${BUILD_DIR}/pyinstaller_dist" \
    --workpath "${BUILD_DIR}/pyinstaller_build" \
    --add-data "${SCRIPT_DIR}/assets:assets" \
    --add-data "${SCRIPT_DIR}/updatymeow:updatymeow" \
    "${SCRIPT_DIR}/run.py"

# 6. Structure AppDir
echo "==> Assembling AppDir structure..."
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/icons/hicolor"

# Copy binary payload
cp -r "${BUILD_DIR}/pyinstaller_dist/updatymeow/"* "${APPDIR}/usr/bin/"
cp -r "${SCRIPT_DIR}/assets" "${APPDIR}/"

# AppRun script
cat << 'EOF' > "${APPDIR}/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${LD_LIBRARY_PATH}"
export APPIMAGE_ORIGINAL_ARGV0="${ARGV0}"
exec "${HERE}/usr/bin/updatymeow" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

# Desktop file with version metadata
cp "${SCRIPT_DIR}/updatymeow.desktop" "${APPDIR}/updatymeow.desktop"
echo "X-AppImage-Version=${VERSION}" >> "${APPDIR}/updatymeow.desktop"
cp "${APPDIR}/updatymeow.desktop" "${APPDIR}/usr/share/applications/"

# Icons
cp "${SCRIPT_DIR}/assets/icons/256x256/updatymeow.png" "${APPDIR}/updatymeow.png"
cp "${SCRIPT_DIR}/assets/icons/256x256/updatymeow.png" "${APPDIR}/.DirIcon"
cp "${SCRIPT_DIR}/assets/icon.svg" "${APPDIR}/updatymeow.svg"

# Copy all icon sizes
for size_dir in "${SCRIPT_DIR}"/assets/icons/*; do
    if [ -d "${size_dir}" ]; then
        s="$(basename "${size_dir}")"
        mkdir -p "${APPDIR}/usr/share/icons/hicolor/${s}/apps"
        cp "${size_dir}/updatymeow.png" "${APPDIR}/usr/share/icons/hicolor/${s}/apps/"
    fi
done

# 7. Package AppImage with appimagetool
TARGET_APPIMAGE="${DIST_DIR}/UpdatyMeow-${VERSION}-x86_64.AppImage"
LATEST_APPIMAGE="${DIST_DIR}/UpdatyMeow-x86_64.AppImage"

echo "==> Packaging ${TARGET_APPIMAGE}..."
ARCH=x86_64 VERSION="${VERSION}" "${APPIMAGETOOL}" "${APPDIR}" "${TARGET_APPIMAGE}"
ln -sf "UpdatyMeow-${VERSION}-x86_64.AppImage" "${LATEST_APPIMAGE}"

echo ""
echo "✓ Successfully built self-contained AppImage!"
echo "  Version: ${VERSION}"
echo "  Artifact: ${TARGET_APPIMAGE}"
echo "  Latest link: ${LATEST_APPIMAGE}"

