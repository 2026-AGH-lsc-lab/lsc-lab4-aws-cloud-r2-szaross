#!/bin/bash
# Endpoint URLs for load testing
# Fill in after deploying with the URLs printed by each deploy script
export LAMBDA_ZIP_URL="https://52h5moavfwi45qw2zoepk7oq540hwutf.lambda-url.us-east-1.on.aws"        # e.g. https://<id>.lambda-url.us-east-1.on.aws
export LAMBDA_CONTAINER_URL="https://to4mb6orcbpmluwh6v2ci6dyji0fgvvu.lambda-url.us-east-1.on.aws"  # e.g. https://<id>.lambda-url.us-east-1.on.aws
export FARGATE_URL="http://lsc-knn-alb-1742105879.us-east-1.elb.amazonaws.com"           # e.g. http://<alb-dns>.us-east-1.elb.amazonaws.com
export EC2_URL="http://44.221.79.18:8080"               # e.g. http://<public-ip>:8080
