#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WRAPPER="$PROJECT_ROOT/src/executable_scripts/mamow"

chmod +x "$WRAPPER"

echo "Installing Hardcoded Launcher to /usr/local/bin/mamow..."
sudo tee /usr/local/bin/mamow > /dev/null <<EOF
#!/usr/bin/env bash
# Hardcoded launcher to prevent symlink venv resolution errors
exec "$WRAPPER" "\$@"
EOF

sudo chmod +x /usr/local/bin/mamow

echo "Installation complete! You can now use the 'mamow' command globally."
