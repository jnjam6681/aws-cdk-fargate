from aws_cdk import (
    aws_ec2 as ec2,
    Stack
)
from constructs import Construct

class SecurityStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        self.mysql_sg = ec2.SecurityGroup(self, 'postgres',
            security_group_name=prj_name+'-mysql-sg',
            vpc=vpc,
            description="SG for Service",
            allow_all_outbound=True
        )
        self.mysql_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(3306), "Allow all traffic")

        client_mysql_sg = ec2.SecurityGroup(self, 'client-mysql',
            security_group_name=prj_name+'-client-mysql-sg',
            vpc=vpc,
            description="SG for Cilent MySQL",
            allow_all_outbound=True
        )

        self.ec2_aws_proxy_sg = ec2.SecurityGroup(self, prj_name+'-rds-proxysg',
            security_group_name=prj_name+'-rds-proxy-sg',
            vpc=vpc,
            description="SG for AWS RDS Proxy Host",
            allow_all_outbound=True
        )
        self.ec2_aws_proxy_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH Access")
        self.ec2_aws_proxy_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(3306), "MySQL Access")

        self.alb_service_sg = ec2.SecurityGroup(self, prj_name+'-alb-frontend-servicesg',
            security_group_name=prj_name+'-alb-frontend-service-sg',
            vpc=vpc,
            allow_all_outbound=True,
            description="SG for ALB Host",
        )
        self.alb_service_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Application Access")

        self.ecs_frontend_service_sg = ec2.SecurityGroup(self, prj_name+'-ecs-frontend-servicesg',
            security_group_name=prj_name+'-ecs-frontend-service-sg',
            vpc=vpc,
            allow_all_outbound=True,
            description="SG for Frontend Host",
        )
        # self.ecs_frontend_service_sg.add_egress_rule(ec2.Peer.any_ipv4(), ec2.Port.all_traffic())
        self.ecs_frontend_service_sg.connections.allow_from_any_ipv4(ec2.Port.all_tcp())