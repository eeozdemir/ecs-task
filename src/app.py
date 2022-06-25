import boto3
import json

print("hello world")
print("initializing client")
client=boto3.client("ecs", region_name="us-east-1")

print("list services")

clusters=services=client.list_clusters()
print(json.dumps(clusters, indent=4, default=str))

services=client.list_services(cluster="arn:aws:ecs:ap-southeast-1:132248825767:cluster/core-edge")
print(json.dumps(services, indent=4, default=str))
