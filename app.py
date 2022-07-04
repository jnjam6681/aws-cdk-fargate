#!/usr/bin/env python3

import aws_cdk as cdk
from stacks.cdn_stack import CDNStack
from stacks.ecs.ecs_cloudfront_stack import CloudFrontStack
from stacks.ecr_stack import ECRStack
from stacks.ecs.ecs_cluster_fargate_stack import ECSClusterFargateStack
from stacks.ecs.ecs_task_fargate_stack import ECSTaskFargateStack
from stacks.rds_stack import RDSStack
from stacks.s3_stack import S3Stack
from stacks.security_stack import SecurityStack
from stacks.vpc_stack import VPCStack

app = cdk.App()

config = app.node.try_get_context("env")
print(config)
buildConfig = app.node.try_get_context(config)
print(buildConfig)

prj_name = app.node.try_get_context("project_name")

env = cdk.Environment(
    account=buildConfig["account"], 
    region=buildConfig["region"]
)

vpc_stack = VPCStack(app, prj_name+"-vpc-stack")
security_stack = SecurityStack(app, prj_name+"-security-stack", vpc=vpc_stack.vpc)

ecr_stack = ECRStack(app, prj_name+"-ecr-stack-"+config, config=config)
s3_stack = S3Stack(app, prj_name+"-s3-stack-"+config, config=config)
cdn_stack = CDNStack(app, prj_name+"-cdn-stack-"+config, s3_bucket=cdk.Fn.import_value(s3_stack.s3_output_1.export_name), config=config)
rds_stack = RDSStack(app, prj_name+"-rds-stack-"+config, vpc=vpc_stack.vpc, config=config, mysql_sg=security_stack.mysql_sg)

ecs_cluster_stack = ECSClusterFargateStack(app, prj_name+"-ecs-cluster-stack-"+config, vpc=vpc_stack.vpc, config=config)
ecs_task_frontend = ECSTaskFargateStack(app, prj_name+"-ecs-task-frontend-stack-"+config, 
    cluster_name=cdk.Fn.import_value(ecs_cluster_stack.ecs_output_1.export_name), 
    cluster_arn=cdk.Fn.import_value(ecs_cluster_stack.ecs_output_2.export_name), 
    ecr_repository=ecr_stack.ecr_frontend, 
    config=config,
    vpc=vpc_stack.vpc, 
    s3_bucket=cdk.Fn.import_value(s3_stack.s3_output_1.export_name),
    alb_sg=security_stack.alb_service_sg,
    ecs_sg=security_stack.ecs_frontend_service_sg
)
cloudfront_stack = CloudFrontStack(app, prj_name+"-cloudfront-stack-"+config, config=config, lb=ecs_task_frontend.alb)

match config:
    case "dev":
        cdk.Tags.of(app).add("environment", "develop")
    case "prod":
        cdk.Tags.of(app).add("environment", "production")
    
cdk.Tags.of(app).add("project", prj_name)

app.synth()
