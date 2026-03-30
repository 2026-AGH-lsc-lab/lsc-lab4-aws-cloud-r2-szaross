#!/bin/bash
# Endpoint URLs for load testing
# Fill in after deploying with the URLs printed by each deploy script
export LAMBDA_ZIP_URL="https://k776td3iwb3txaileuxoqw7ce40arzjg.lambda-url.us-east-1.on.aws"        # e.g. https://<id>.lambda-url.us-east-1.on.aws
export LAMBDA_CONTAINER_URL="https://yb326yjysjnoqghc67lvi6rgya0qsccg.lambda-url.us-east-1.on.aws"  # e.g. https://<id>.lambda-url.us-east-1.on.aws
export FARGATE_URL="http://lsc-knn-alb-243612631.us-east-1.elb.amazonaws.com"           # e.g. http://<alb-dns>.us-east-1.elb.amazonaws.com
export EC2_URL="http://98.93.122.239:8080"               # e.g. http://<public-ip>:8080
