from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs
)
from constructs import Construct

class ECSClusterFargateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        match config:
            case 'dev':
                cluster = ecs.Cluster(self, prj_name+"-ecs-cluster-"+config,
                    vpc=vpc,
                    enable_fargate_capacity_providers=True,
                    cluster_name=prj_name+"-ecs-cluster-"+config
                )

                # cluster.add_capacity("spot-dev",
                #     max_capacity=2,
                #     min_capacity=2,
                #     desired_capacity=2,
                #     instance_type=ec2.InstanceType("t3.small"),
                #     spot_price="0.0735",
                #     # Enable the Automated Spot Draining support for Amazon ECS
                #     spot_instance_draining=True,
                # )
            
            case 'prod':
                cluster = ecs.Cluster(self, prj_name+"-ecs-cluster-"+config,
                    vpc=vpc,
                    enable_fargate_capacity_providers=True,
                    cluster_name=prj_name+"-ecs-cluster-"+config,
                    container_insights=True,
                )

                # cluster.add_capacity("spot-prod",
                #     max_capacity=2,
                #     min_capacity=2,
                #     desired_capacity=2,
                #     instance_type=ec2.InstanceType("t3.medium"),
                #     spot_price="0.0735",
                #     # Enable the Automated Spot Draining support for Amazon ECS
                #     spot_instance_draining=True,
                # )

        self.ecs_output_1 = CfnOutput(self, 'ecs-output-1',
            value=cluster.cluster_name,
            export_name='ecs-cluster-name-'+config
        )

        self.ecs_output_2 = CfnOutput(self, 'ecs-output-2',
            value=cluster.cluster_arn,
            export_name='ecs-cluster-arn-'+config
        )