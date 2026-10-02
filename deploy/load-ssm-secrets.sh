#!/bin/bash
# deploy/load-ssm-secrets.sh  (OPTIONAL - needs Parameter Store permissions)
# Builds the server's .env from AWS Systems Manager Parameter Store instead of
# keeping secrets in a file you typed. Expects SecureString parameters under /bank/:
#   /bank/MONGO_USER  /bank/MONGO_PASSWORD  /bank/JWT_SECRET  /bank/API_KEY  /bank/CORS_ORIGINS
# The EC2 server needs an IAM role allowing ssm:GetParametersByPath on /bank/*.
#   bash deploy/load-ssm-secrets.sh
set -euo pipefail
aws ssm get-parameters-by-path --path /bank/ --with-decryption --region us-east-1 \
  --query 'Parameters[].[Name,Value]' --output text |
  while read -r name value; do echo "${name#/bank/}=${value}"; done > .env
echo "MONGO_URL=unused-in-docker" >> .env
chmod 600 .env
echo "Loaded $(wc -l < .env) settings from Parameter Store into .env"
