
# general
mkfile_path := $(abspath $(firstword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
current_abs_path := $(subst Makefile,,$(mkfile_path))

# pipeline constants
# PROJECT_NAME
project_name := "2025-autumn-bfi"
project_dir := "$(current_abs_path)"

# environment variables
include .env

# Check required environment variables
ifeq ($(DATA_DIR),)
    $(error DATA_DIR must be set in .env file)
endif


# Build Docker image
# Global mount for data directory
mount_data := -v $(DATA_DIR):/project/data

.PHONY: build-only run-interactive run-notebooks test-pipeline clean

# Build Docker image
build-only:
	docker compose build

build-run: build-only
	docker run -p 8501:8501 2025-autumn-bfi-app

run-only:
	docker run -p 8501:8501 2025-autumn-bfi-app

quick-clean:
	docker compose down --remove-orphans

deep-clean:
	docker compose down --rmi all --volumes --remove-orphans