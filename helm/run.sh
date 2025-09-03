#!/bin/sh
APP_NAME=elegibility

helm template . --name-template ${APP_NAME} \
  --include-crds