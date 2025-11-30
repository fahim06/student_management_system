#!/bin/bash

# Exit on error
set -e

pip install -r requirements.txt
python manage.py collectstatic --noinput