#!/bin/bash

# zephyr-docker-helper.sh
#
# A wrapper script to run Zephyr's 'west' tool inside the official Docker container.
# This keeps your host system 100% clean, as all tools and the SDK
# are contained within the Docker image.

# --- CONFIGURATION ---
# You can update this to a specific version tag if you need to.
# See available tags: https://hub.docker.com/r/zephyrprojectrtos/ci/tags
# Alternatively, override via environment variable: ZEPHYR_IMAGE_NAME
# Recommended: zephyrprojectrtos/ci:latest (minimal, no VNC noise)
IMAGE_NAME="${ZEPHYR_IMAGE_NAME:-zephyrprojectrtos/ci:latest}"

# SDK path inside the container (based on common installation; override if needed)
SDK_PATH="/opt/toolchains/zephyr-sdk-0.17.4"

# Get the full path to the directory this script is in, and 'cd' there.
# This ensures the script can be run from anywhere.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# This is the Zephyr workspace root (where .west is)
readonly WORKSPACE_DIR="$SCRIPT_DIR"

# --- HELPER FUNCTIONS ---

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker to use this script."
  exit 1
fi

# Usage/help function
usage() {
  echo "Usage: $0 [COMMAND] [OPTIONS]"
  echo ""
  echo "This script runs Zephyr's 'west' tool inside a Docker container."
  echo "Special commands (not passed to 'west'):"
  echo "  setup         Set up a new Zephyr workspace from scratch (runs 'west init' and 'west update')."
  echo "                Usage: $0 setup [-m MANIFEST_URL] [--mr REVISION]"
  echo "                Default: -m https://github.com/zephyrproject-rtos/zephyr --mr main"
  echo "  pull          Download or update the Docker image."
  echo "  clean         Clean local build artifacts (build/, twister-out/, zephyr/.cache/)."
  echo "  shell         Enter an interactive shell inside the Docker container."
  echo "  help          Show this help message."
  echo ""
  echo "All other commands are passed to 'west' (e.g., '$0 build -b nrf52840dk_nrf52840')."
  echo "For 'flash' or 'debug', the container runs with privileged access (Linux only)."
  echo ""
  echo "Environment variables:"
  echo "  ZEPHYR_IMAGE_NAME  Override the Docker image name/tag (default: $IMAGE_NAME)."
  echo "  Alternatively, you can use the GHCR image: ghcr.io/zephyrproject-rtos/ci:latest"
  exit 0
}

# --- SPECIAL COMMANDS (Not passed to 'west') ---

# Handle no arguments or help
if [ $# -eq 0 ] || [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  usage
fi

# 'setup' command:
# Sets up a new Zephyr workspace from scratch using 'west init' and 'west update' inside Docker.
if [ "$1" == "setup" ]; then
  shift  # Shift to process additional arguments

  # Default values for west init
  MANIFEST_URL="https://github.com/zephyrproject-rtos/zephyr"
  MANIFEST_REV="main"

  # Parse optional arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -m)
        MANIFEST_URL="$2"
        shift 2
        ;;
      --mr)
        MANIFEST_REV="$2"
        shift 2
        ;;
      *)
        echo "Unknown option: $1"
        usage
        ;;
    esac
  done

  # Check if workspace is already initialized
  if [ -d ".west" ]; then
    echo "Error: Workspace already initialized (.west directory exists). Run 'clean' first or use a new directory."
    exit 1
  fi

  echo "Setting up Zephyr workspace from scratch..."
  echo "Pulling Docker image: $IMAGE_NAME"
  docker pull "$IMAGE_NAME" || { echo "Failed to pull image."; exit 1; }

  # Build core Docker command with SDK env vars
  DOCKER_BASE=(
    "docker" "run" "--rm"
    "-v" "${WORKSPACE_DIR}:/workspace"
    "-w" "/workspace"
    "--user" "$(id -u):$(id -g)"
    "-e" "ZEPHYR_TOOLCHAIN_VARIANT=zephyr"
    "-e" "ZEPHYR_SDK_INSTALL_DIR=${SDK_PATH}"
    "${IMAGE_NAME}"
  )

  # Run 'west init'
  echo "Running: west init -m $MANIFEST_URL --mr $MANIFEST_REV"
  "${DOCKER_BASE[@]}" "west" "init" "-m" "$MANIFEST_URL" "--mr" "$MANIFEST_REV" || { echo "west init failed."; exit 1; }

  # Run 'west update' (source env.sh for completeness)
  echo "Running: west update"
  "${DOCKER_BASE[@]}" "bash" "-c" "source /workspace/zephyr/zephyr-env.sh && exec west update" || { echo "west update failed."; exit 1; }

  echo "Setup complete. Workspace initialized."
  exit 0
fi

# 'pull' command:
# Use this to download or update the Docker build environment.
if [ "$1" == "pull" ]; then
  echo "Pulling Docker image: $IMAGE_NAME"
  docker pull "$IMAGE_NAME"
  exit $?
fi

# 'clean' command:
# This runs locally to clean up build artifacts.
if [ "$1" == "clean" ]; then
  echo "Cleaning local build artifacts (build/, twister-out/, zephyr/.cache/)..."
  rm -rf build/ twister-out/ zephyr/.cache/
  echo "Clean complete."
  exit $?
fi

# 'shell' command:
# Enter an interactive shell in the container for debugging or manual commands.
# Sets SDK env vars and sources zephyr-env.sh.
if [ "$1" == "shell" ]; then
  echo "Starting interactive shell in Docker container..."
  DOCKER_CMD=(
    "docker" "run" "--rm" "-it"
    "-v" "${WORKSPACE_DIR}:/workspace"
    "-w" "/workspace"
    "--user" "$(id -u):$(id -g)"
    "-e" "ZEPHYR_TOOLCHAIN_VARIANT=zephyr"
    "-e" "ZEPHYR_SDK_INSTALL_DIR=${SDK_PATH}"
    "${IMAGE_NAME}"
    "bash" "-c" "source /workspace/zephyr/zephyr-env.sh && exec /bin/bash"
  )
  exec "${DOCKER_CMD[@]}"
fi

# --- DOCKER RUN ---
# All other commands are passed directly to 'west' inside the container.

echo "--- Zephyr Docker Build ---"

# Build the core docker run command
# --rm: Automatically remove the container when it exits.
# -v: Mount the current directory (your workspace) into '/workspace' in the container.
# -w: Set the working directory inside the container to '/workspace'.
# --user: Run as your host user/group. This is CRITICAL to avoid
#         'root'-owned files being created in your workspace.
DOCKER_CMD=(
  "docker" "run" "--rm"
  "-v" "${WORKSPACE_DIR}:/workspace"
  "-w" "/workspace"
  "--user" "$(id -u):$(id -g)"
  "-e" "ZEPHYR_TOOLCHAIN_VARIANT=zephyr"
  "-e" "ZEPHYR_SDK_INSTALL_DIR=${SDK_PATH}"
)

# 'flash' command (and 'debug') is special.
# It needs access to your host's USB devices (J-Link, etc.).
# This is complex and platform-specific (this setup is for Linux).
# Warning: Use with caution, as --privileged grants broad access.
if [ "$1" == "flash" ] || [ "$1" == "debug" ]; then
  echo ">>> WARNING: 'flash'/'debug' requires privileged host access. <<<"
  # --privileged: Gives the container full access to host devices.
  # -v /dev:/dev: Mounts the host's device tree.
  DOCKER_CMD+=(
    "--privileged"
    "-v" "/dev:/dev"
  )
fi

# Add the image name and wrap the command:
# Use bash to set SDK env vars, source zephyr-env.sh, then run 'west' with args.
# The '--' separates bash args from west args.
DOCKER_CMD+=(
  "${IMAGE_NAME}"
  "bash" "-c" "source /workspace/zephyr/zephyr-env.sh && exec west \"\$@\"" "--"
)
DOCKER_CMD+=( "$@" )

# --- EXECUTE ---
# Run the command we just built.
# 'exec' replaces this script process with the docker process.
echo "Running: ${DOCKER_CMD[*]}"
exec "${DOCKER_CMD[@]}"
