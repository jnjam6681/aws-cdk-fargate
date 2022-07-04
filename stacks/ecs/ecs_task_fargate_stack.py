import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
)
from constructs import Construct

class ECSTaskFargateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cluster_name: str ,cluster_arn: str, ecr_repository: ecr.Repository, config: str, vpc: ec2.Vpc, alb_sg: ec2.SecurityGroup, ecs_sg: ec2.SecurityGroup, s3_bucket: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        bucket = s3.Bucket.from_bucket_name(self, 's3-bucket', s3_bucket)

        self.alb = elbv2.ApplicationLoadBalancer(self, prj_name+"-alb-"+config,
            load_balancer_name=prj_name+"-"+config,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            internet_facing=True,
            security_group=alb_sg
        )

        target_group_http = elbv2.ApplicationTargetGroup(self, "target-group",
            target_group_name=prj_name+"-frontend-"+config,
            port=80,
            vpc=vpc,
            target_type=elbv2.TargetType.IP,
            protocol=elbv2.ApplicationProtocol.HTTP,
            deregistration_delay=cdk.Duration.seconds(5),
        )

        target_group_http.configure_health_check(
            interval=Duration.seconds(60),
            path="/",
            timeout=Duration.seconds(5),
            protocol=elbv2.ApplicationProtocol.HTTP,
        )

        listener = self.alb.add_listener(prj_name+"-alb-listener-"+config,
            open=True,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
        )

        listener.add_target_groups(prj_name+"-alb-listener-target-group-"+config,
            target_groups=[target_group_http]
        )

        cluster = ecs.Cluster.from_cluster_attributes(self, prj_name+"-cluster-"+config, 
            cluster_name=cluster_name,
            cluster_arn=cluster_arn,
            security_groups=[alb_sg],
            vpc=vpc
        )

        task_role = iam.Role(self, prj_name+"-task-role-"+config,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            role_name=prj_name+"-task-role-"+config,
        )

        task_role.attach_inline_policy(
            iam.Policy(self, prj_name+"-task-policy-"+config,
                statements=[iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["s3:*"],
                    resources=["*"]
                )]
            )
        )

        fargate_task_definition = ecs.FargateTaskDefinition(self, prj_name+"-task-frontend-"+config,
            family=prj_name+"-frontend-"+config,
            memory_limit_mib=512,
            cpu=256,
            execution_role=task_role,
        )

        match config:
            case "dev":
                specific_container = fargate_task_definition.add_container(prj_name+"-frontend-"+config,
                    container_name=prj_name+"-frontend-"+config,
                    image=ecs.ContainerImage.from_ecr_repository(ecr_repository),
                    memory_limit_mib=256,
                    cpu=128,
                    environment_files=[
                        ecs.EnvironmentFile.from_bucket(bucket, "assets/env-dev.env")],
                    logging=ecs.LogDriver.aws_logs(
                        stream_prefix="ecs",
                    ),
                )
            case "prod":
                specific_container = fargate_task_definition.add_container(prj_name+"-frontend-"+config,
                    image=ecs.ContainerImage.from_ecr_repository(ecr_repository),
                    memory_limit_mib=256,
                    cpu=128,
                    environment_files=[
                        ecs.EnvironmentFile.from_bucket(bucket, "assets/env-prod.env")],
                    logging=ecs.LogDriver.aws_logs(
                        stream_prefix="ecs",
                    ),
                )

        port_mapping = ecs.PortMapping(
            container_port=80,
            # host_port=80,
            protocol=ecs.Protocol.TCP
        )
        specific_container.add_port_mappings(port_mapping)

        match config:
            case "dev":
                ecs_service = ecs.FargateService(self, prj_name+"-frontend-"+config,
                    cluster=cluster,
                    # service_name=prj_name+"-frontend",
                    task_definition=fargate_task_definition,
                    assign_public_ip=False,
                    desired_count=1,
                    # circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True)
                    capacity_provider_strategies=[ecs.CapacityProviderStrategy(
                        capacity_provider="FARGATE_SPOT",
                        weight=1
                    )
                    ],
                    security_groups=[ecs_sg],
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                    ),
                    health_check_grace_period=cdk.Duration.seconds(0),
                    min_healthy_percent=50,
                    max_healthy_percent=200,
                )

                ecs_service.attach_to_application_target_group(target_group_http)

            case "prod":
                ecs_service = ecs.FargateService(self, prj_name+"-frontend-"+config,
                    cluster=cluster,
                    # service_name=prj_name+"-frontend",
                    task_definition=fargate_task_definition,
                    assign_public_ip=False,
                    desired_count=2,
                    # circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True)
                    capacity_provider_strategies=[ecs.CapacityProviderStrategy(
                        capacity_provider="FARGATE_SPOT",
                        weight=2
                    ), ecs.CapacityProviderStrategy(
                        capacity_provider="FARGATE",
                        weight=1
                    )
                    ],
                    security_groups=[ecs_sg],
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                    ),
                    health_check_grace_period=cdk.Duration.seconds(0),
                    min_healthy_percent=50,
                    max_healthy_percent=200,
                )

                ecs_service.attach_to_application_target_group(target_group_http);

                scaling = ecs_service.auto_scale_task_count(
                    min_capacity=1,
                    max_capacity=10
                )

                scaling.scale_on_cpu_utilization("CpuScaling",
                    target_utilization_percent=80
                )

                scaling.scale_on_memory_utilization("MemoryScaling",
                    target_utilization_percent=80
                )

                scaling.scale_on_request_count("RequestScaling",
                    requests_per_target=10000,
                    target_group=target_group_http
                )