#!/bin/bash
cd "${0%/*}"
OUTPUT="${1:-TA-hetrix.spl}"
pip install --upgrade --no-dependencies -t lib -r lib/requirements.txt
rm -rf lib/*.dist-info
tar -cpzf $OUTPUT --exclude=.* --exclude=package.json --overwrite ../TA-hetrix 