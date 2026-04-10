#!/bin/bash
ecflow_client --init=$$
set -eux
trap 'ecflow_client --abort; exit 1' ERR EXIT
