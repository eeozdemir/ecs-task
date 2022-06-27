# ECS-Services-Lifecycle
This service manages pos-workers for their lifecycle with serverless mindset meaning that each idle services will tear down based on configured time window to decrease the computation cost in AWS ECS.

# Environmental variables
Variable Name | Description | Example
--- | --- | ---
clusterArn | ECS cluster ARN which the service would watch on it | arn:aws:ecs:us-east-1:132248825767:cluster/hamid-testlab-staging
servicePrefix | The service prefix which we will keep track of its activity and idle time in case that we want to start or tear it down | pos-worker
idleSeconds | Idle timeout for each service in seconds. if the service doesn't receive the request on app's hook api after this timeout the service desiredCount will set to zero | 1800
port | The `TCP` port number which application will listen on it | 80


