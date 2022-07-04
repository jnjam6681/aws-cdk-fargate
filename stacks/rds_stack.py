import json
import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_logs as logs,
    # aws_ssm as ssm,
    aws_secretsmanager as sm,
    Stack
)
from constructs import Construct

class RDSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, config: str, mysql_sg: ec2.SecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        rds_creds = sm.Secret(self, "db-secret-"+config,
            secret_name=prj_name+'/'+config+'/rds-secret',
            generate_secret_string=sm.SecretStringGenerator(
                include_space=False,
                password_length=12,
                generate_string_key='password',
                exclude_punctuation=True,
                secret_string_template=json.dumps(
                    {'username': 'postgres'}
                ),
            )
        )

        parameter_group = rds.ParameterGroup(self, prj_name+"-mysql-parameter-"+config,
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_26),
            description="Parameter for Mysql"
        )

        match config:
            case 'dev':

                db_mysql = rds.DatabaseInstance(self, prj_name+"-rds-mysql-dev",
                    instance_identifier=prj_name+'-'+config,
                    engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_26),
                    # database_name='aprilia',
                    instance_type=ec2.InstanceType.of(
                        ec2.InstanceClass.BURSTABLE3, 
                        ec2.InstanceSize.MICRO),
                    credentials=rds.Credentials.from_secret(rds_creds),
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PUBLIC
                    ),
                    vpc=vpc,
                    multi_az=False,
                    # storage_encrypted=True,
                    storage_type=rds.StorageType.GP2,
                    allocated_storage=30,
                    max_allocated_storage=40,
                    deletion_protection=True,
                    backup_retention=cdk.Duration.days(7),
                    monitoring_interval=cdk.Duration.seconds(60),
                    cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
                    enable_performance_insights=False,
                    cloudwatch_logs_exports=["error", "general", "slowquery", "audit"],
                    # auto_minor_version_upgrade=True,
                    removal_policy=cdk.RemovalPolicy.SNAPSHOT,
                    delete_automated_backups=True,
                    parameter_group=parameter_group,
                )
            
            case 'prod':
                db_mysql = rds.DatabaseInstance(self, prj_name+"-rds-mysql-prod",
                    instance_identifier=prj_name+'-'+config,
                    engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_26),
                    # database_name='aprilia',
                    instance_type=ec2.InstanceType.of(
                        ec2.InstanceClass.BURSTABLE3, 
                        ec2.InstanceSize.MEDIUM),
                    credentials=rds.Credentials.from_secret(rds_creds),
                    vpc_subnets=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                    ),
                    vpc=vpc,
                    multi_az=False,
                    # storage_encrypted=True,
                    storage_type=rds.StorageType.GP2,
                    allocated_storage=30,
                    max_allocated_storage=40,
                    deletion_protection=True,
                    backup_retention=cdk.Duration.days(7),
                    monitoring_interval=cdk.Duration.seconds(60),
                    cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
                    enable_performance_insights=True,
                    cloudwatch_logs_exports=["error", "general", "slowquery", "audit"],
                    # auto_minor_version_upgrade=True,
                    removal_policy=cdk.RemovalPolicy.SNAPSHOT,
                    delete_automated_backups=True,
                    parameter_group=parameter_group,
                )

        db_mysql.connections.allow_default_port_from_any_ipv4()
        db_mysql.connections.allow_default_port_from(mysql_sg, "Allow traffic from ...")

        #SSM Parameter
        # ssm.StringParameter(self, 'db-host',
        #     parameter_name='/'+prj_name+'/db-host',
        #     string_value=db_postgres.cluster_endpoint.hostname
        # )

        # ssm.StringParameter(self,'db-name',
        #     parameter_name='/'+prj_name+'/db-name',
        #     string_value=prj_name
        # )

        self.rds_output_1 = CfnOutput(self, 'rds-output-1',
            value=f"{rds_creds.secret_value}",
            description="secret value",
        )

        self.rds_output_2 = CfnOutput(self, 'rds-output-2',
            value=db_mysql.db_instance_endpoint_address,
            # description="secret value",
            export_name='rds-instance-endpoint-address-'+config
        )

        # self.rds_output_3 = CfnOutput(self, 'rds-output-3',
        #     value=db_mysql.instance_endpoint,
        #     # description="secret value",
        #     export_name='rds-name-'+team
        # )
