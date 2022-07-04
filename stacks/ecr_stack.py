from aws_cdk import (
    CfnOutput,
    CfnTag,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    Stack
)
from constructs import Construct

class ECRStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        self.ecr_frontend = ecr.Repository(self, prj_name+"-ecr-frontend-"+config,
            repository_name=prj_name+"-frontend-"+config,
            image_scan_on_push=False,
            # image_tag_mutability="imageTagMutability",
        )

        self.ecr_output_1 = CfnOutput(self, 'ecr-output-1',
            value=self.ecr_frontend.repository_uri,
            # description="secret value",
            export_name='ecr-frontend-'+config
        )