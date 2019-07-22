# Public targets
.PHONY: clean help image push tests
# Private targets
.PHONY: _dev_image _requirements

.DEFAULT_GOAL = help

_BOLD := \e[1m
_NORMAL := \e[0m
define HELP_CONTENT
  ${_BOLD}clean${_NORMAL}  Clean the Docker image and the local build.
  ${_BOLD}help${_NORMAL}   Display this help.
  ${_BOLD}image${_NORMAL}  Build the production-ready Docker image.
  ${_BOLD}push${_NORMAL}   Push the container image to the registry.
  ${_BOLD}tests${_NORMAL}  Run the tests suite.
endef
export HELP_CONTENT

help:
	@echo -e "The following targets are available with ${_BOLD}make${_NORMAL} in this project:"
	@echo -e "$$HELP_CONTENT"


PWD = $(shell pwd)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
GIT_BRANCH_CLEANED = $(shell echo ${GIT_BRANCH} | sed -Ee 's|origin/||g; s|[^a-zA-Z0-9_.-]+|-|g')
GIT_COMMIT = $(shell git log -1 --pretty="%h" --abbrev=6)

SUDO = sudo --preserve-env

CONTAINER_IMAGE_NAME_DEV = akaoj/plimni:dev
CONTAINER_IMAGE_NAME_PROD = akaoj/plimni:${GIT_BRANCH_CLEANED}-${GIT_COMMIT}
CONTAINER_IMAGE_NAME_PROD_ALIAS = akaoj/plimni:${GIT_BRANCH_CLEANED}
REGISTRY_URL = docker.io


_requirements:
	@command -v docker &>/dev/null || { echo 'You need Docker, please install it first'; exit 1; }

_dev_image: _requirements
	${SUDO} docker build -t ${CONTAINER_IMAGE_NAME_DEV} -f Dockerfile.dev .

define container_make
    ${SUDO} docker run -it --rm -v ${PWD}:/code:Z --name plimni ${CONTAINER_IMAGE_NAME_DEV} "make --makefile Makefile.container $1"
endef


clean:
	-${SUDO} docker rmi ${CONTAINER_IMAGE_NAME_DEV}
	-${SUDO} docker rmi ${CONTAINER_IMAGE_NAME_PROD}
	-${SUDO} docker rmi ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD}
	-${SUDO} docker rmi ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD_ALIAS}

image:
	${SUDO} docker build -t ${CONTAINER_IMAGE_NAME_PROD} .

push:
	${SUDO} docker tag ${CONTAINER_IMAGE_NAME_PROD} ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD}
	${SUDO} docker push ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD}
	${SUDO} docker tag ${CONTAINER_IMAGE_NAME_PROD} ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD_ALIAS}
	${SUDO} docker push ${REGISTRY_URL}/${CONTAINER_IMAGE_NAME_PROD_ALIAS}

tests: _dev_image
	$(call container_make,tests)
