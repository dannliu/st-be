#!/bin/bash

gunicorn -t 120 -w 1 -b 0.0.0.0:8100 colleague.app:app --access-logfile - --error-logfile -

