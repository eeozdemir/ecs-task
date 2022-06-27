import logging
import boto3
import json
import sys
import os
import flask
import time
from threading import Thread, Lock

mutex=Lock()
server=flask.Flask(__name__)
clusterArn="arn:aws:ecs:us-east-1:132248825767:cluster/hamid-testlab-staging"
servicePrefix="pos-worker"
idleSeconds=10
serviceArnPrefix="arn:aws:ecs:us-east-1:132248825767:service/hamid-testlab-staging/"
region="us-east-1"
port=8080

# service hash is local dictionary to keep track of services defined in ECS
# Hash Structure:
# { 
#    [serviceName: str]: {
#       lastActivitySeen: int,
#       desiredCount: int,
#    }
# }
serviceState: dict= {}

def readEnvs() -> None:
    global clusterArn
    global servicePrefix
    global idleSeconds
    global serviceArnPrefix
    global region
    global port

    clusterArn=os.environ["clusterArn"]
    servicePrefix=os.environ["servicePrefix"]
    idleSeconds=int(os.environ["idleSeconds"])
    port=int(os.environ["port"])
    serviceArnPrefix=extractServiceArnPrefixFrom(clusterArn)
    region=extractRegionFrom(clusterArn)

def extractRegionFrom(clusterArn: str) -> str:
    return clusterArn.split(":")[3]

def extractServiceArnPrefixFrom(clusterArn: str) -> str:
    _, vendor, svc, region, accountId, resName=clusterArn.split(":")
    clusterName=resName.split("/")[1]
    return f"arn:{vendor}:{svc}:{region}:{accountId}:service/{clusterName}/"

def extractServiceNameFrom(serviceArn: str) -> str:
    return serviceArn.split("/")[2]

def checkServiceStateConsistent(describedService: list) -> bool:
    serviceName=describedService["services"][0]["serviceName"]
    desiredCount=describedService["services"][0]["desiredCount"]

    return desiredCount==serviceState.get(serviceName, {}).get("desiredCount", -1)

def addOrUpdateService(serviceName: str, describedService: dict, updateLastActivitySeen: bool = False) -> None:
        mutex.acquire()
        serviceState[serviceName] = {
            "lastActivitySeen": int(time.time()),
            "desiredCount": describedService["services"][0]["desiredCount"],
        }
        mutex.release()

def scanServices() -> None:
    global region

    client=boto3.client("ecs", region_name=region)
    paginator = client.get_paginator('list_services')
    pages = paginator.paginate(cluster=clusterArn,
        PaginationConfig={
            'PageSize':100
        })

    for page in pages:
        for serviceArn in page['serviceArns']:
            server.logger.info(f"checking {serviceArn}")
            serviceName=extractServiceNameFrom(serviceArn)
            if not serviceName.startswith(servicePrefix):
                continue
            describedService = describeService(serviceArn, client)
            if not checkServiceStateConsistent(describedService):
                addOrUpdateService(serviceName, describedService)

def describeService(serviceArn:str, client: any=None) -> any:
    if client == None:
        client=boto3.client("ecs", region_name=region)
    
    return client.describe_services(
        cluster=clusterArn,
        services=[serviceArn]
    )   

def shutdown(serviceName: str) -> None:
    server.logger.info(f"shutting down {serviceArnPrefix+serviceName}")
    client=boto3.client("ecs", region_name=region)
    client.update_service(
            cluster = clusterArn,
            service = serviceArnPrefix+serviceName,
            desiredCount = 0
        )

def start(serviceName: str) -> None:
    server.logger.info(f"starting {servicePrefix+serviceName}")
    client=boto3.client("ecs", region_name=region)
    client.update_service(
            cluster = clusterArn,
            service = serviceArnPrefix+serviceName,
            desiredCount = 1
        )

def workerServiceScanner() -> None:
    first=True
    while True:
        scanServices()
        if first:
            Thread(target=workerIdledServiceShutdown).start()
            first=False
        time.sleep(60)

def workerIdledServiceShutdown() -> None:
    while True:
        server.logger.info(json.dumps(serviceState, indent=4, default=str))
        for serviceName in serviceState:
            if serviceState[serviceName]["desiredCount"]==0:
                continue
            
            if int(time.time()) > serviceState[serviceName]["lastActivitySeen"]+idleSeconds:
                shutdown(serviceName)

        time.sleep(60)

@server.route("/v1/hook/<environment>/pos-worker/<posWorker>")
def hook(environment:str, posWorker:str):
    servicePosWorker=f"{posWorker}-{environment}" if environment != "staging" else posWorker
    serviceArn=f"{servicePrefix}-{servicePosWorker}"
    try:
        describedService=describeService(serviceArn)
    except:
        return {"code":404, "message":"service not found"}, 404
    
    if not describedService["services"]:
        return {"code":404, "message":"service not found"}, 404

    oldDesiredCount=describedService["services"][0]["desiredCount"]
    describedService["services"][0]["desiredCount"]=1
    addOrUpdateService(describedService["services"][0]["serviceName"], describedService)
    if oldDesiredCount==0:
        start(describedService["services"][0]["serviceName"])

    if oldDesiredCount>0:
        return {"code":200, "message":"running"}, 200
    
    return {"code":202, "message": "The service was slept. going to start it"}, 202

@server.route("/healthz")
def healthz():
    return {
        "code": 200,
        "message": "It works"
    }, 200

def main() -> int:
    readEnvs()
    server.logger.setLevel(logging.INFO)
    server.logger.info("hello world")
    Thread(target=workerServiceScanner).start()
    server.run("0.0.0.0", port)
    return 1

if __name__ == "__main__":
    sys.exit(main())