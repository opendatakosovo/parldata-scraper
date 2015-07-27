#!/usr/bin/env bash
source ./venv/bin/activate
if [ "$#" -ne 5 ]
then
    echo "Invalid number of parameters."
else
    python run.py --countries $1 --people $2 --votes $3 --time_out $4 --time_out_seconds $5
fi

