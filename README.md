# ECS-Services-Lifecycle
This service manages pos-workers for their lifecycle with serverless mindset meaning that each idle services will tear down based on configured time window to decrease the computation cost in AWS ECS.

# Environmental variables
Here are the environmental variables which application accept them as the config. you can set this env for the application for runtime
<br/>
<br/>

Variable Name | Description | Example
--- | --- | ---
clusterArn | ECS cluster ARN which the service would watch on it | arn:aws:ecs:us-east-1:132248825767:cluster/hamid-testlab-staging
servicePrefix | The service prefix which we will keep track of its activity and idle time in case that we want to start or tear it down | pos-worker
idleSeconds | Idle timeout for each service in seconds. if the service doesn't receive the request on app's hook api after this timeout the service desiredCount will set to zero | 1800
port | The TCP port number which application will listen on it | 80


# How it works
Based on `clusterArn` env it set and based on appropriate Task Role set for the task in task definition it connects to AWS ECS API server and start to looking for the services starts with `servicePrefix` string set in env and not ending with `-demo`. At first it assumes `idleSeconds` as a timeout for those running services (desiredCount > 0) and based on each request receives by hook route it refreshes the idle second. Right after idleSeconds exceeds this application will update the service desiredCount to zero to stop the service.

# API

**Request:**

```
GET /v1/hook/{environment}/pos-worker/{pos-worker-name}
```
Here we have two inputs one `environment` like staging, dev1, dev2 and demo and the second one `pos-worker-name` which you can send dooshi, omnivore and etc. you don't need to mention the pos-worker as prefix for the worker's name

**Response:**

In case the service was been already running you will get 200 HTTP status code with json format below as the response body:

```
{
    "code": 200,
    "message": "running"
}
```

In case the service been stopped you will receive the response below and at the same time the service will go to start in the background asynchronously, this time you will receive 202 HTTP status code with json format below as the response body

```
{
    "code": 202,
    "message": "The service was slept. going to start it"
}
```

and finally in case the service doesn't exist you will receive the response 404 HTTP status code with the reponse body in json format below:

```
{
    "code": 404,
    "message": "service not found"
}
```