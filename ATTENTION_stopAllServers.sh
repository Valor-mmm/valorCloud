#!/bin/zsh

# Specify the directory containing subfolders with docker-compose files
directory="./servers"

# ANSI Color Codes
GREEN="\033[0;32m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
YELLOW="\033[0;33m"
RED="\033[0;31m"


# Check if the directory exists
if [ ! -d "$directory" ]; then
  echo -e "${RED}Directory '$directory' does not exist.${RESET}"
  exit 1
fi

echo -e "${RED}Stopping ALL servers in directory ${CYAN}$directory${RED}:${reset}\n\n"

# Iterate over subfolders in the specified directory
for subfolder in "$directory"/*; do
  if [ -d "$subfolder" ]; then
    echo -e "Entering directory: ${CYAN}$subfolder${RESET}"
    cd "$subfolder" || continue

    # Check if a docker-compose.yml file exists in the subfolder
    if [ -f "docker-compose.yaml" ]; then
      # Start the Docker containers in detached mode (-d)
      docker-compose down
      echo -e "${GREEN}Docker containers ${RED}stopped${GREEN} in ${CYAN}$subfolder${RESET}\n"
    else
      echo -e "${YELLOW}No docker-compose.yaml file found in $subfolder${RESET}\n"
    fi

    # Return to the original directory
    cd - >/dev/null
  fi
done

echo -e "${MAGENTA}Stopped all servers ${GREEN}successfully${RESET}"
