from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class VPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        self.vpc = ec2.Vpc(self, 'vpc',
            cidr="172.32.0.0/21",
            vpc_name=prj_name+'-vpc',
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24
                ),
            ],
            nat_gateways=1
        )

        CfnOutput(self,
            "vpc-output",
            value=self.vpc.vpc_id,
            export_name="vpc-id")