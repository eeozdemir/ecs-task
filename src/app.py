import sys
import boto3
import json
import sys
import os
import flask

def main():
    print("hello world")
    print("initializing client")
    client=boto3.client("ecs", region_name="us-east-1")

    response = client.update_service(
            service = "arn:aws:ecs:us-east-1:132248825767:service/hamid-testlab-staging/nginx",
            desiredCount = 0
        )
        
    print(json.dumps(response, indent=4, default=str))

if __name__ == "__main__":
    sys.exit(main())