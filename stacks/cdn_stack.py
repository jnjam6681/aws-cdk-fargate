from aws_cdk import (
    CfnOutput,
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cdn,
    aws_cloudfront_origins as origin,
    # aws_certificatemanager as acm,
    aws_iam as iam,
)
from constructs import Construct 

class CDNStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, s3_bucket: str, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        # acm_arn="arn:aws:acm:us-east-1:847796370246:certificate/d97ef3af-c03d-4a5c-8e99-ea8897392a2e"
        bucket = s3.Bucket.from_bucket_name(self, 's3-bucket', s3_bucket)
        # certificate = acm.Certificate.from_certificate_arn(self, "Certificate", acm_arn)

        origin_access_identity = cdn.OriginAccessIdentity(self, prj_name+"-origin-access-dentity-"+config,
            comment=prj_name+"-origin-access-dentity-"+config
        )

        match config:
            case "dev":
                self.cdn_id = cdn.Distribution(self, prj_name+'-cdn-s3-image-'+config,
                    default_behavior=cdn.BehaviorOptions(
                        origin=origin.S3Origin(
                            bucket,
                            origin_access_identity=origin_access_identity
                        ),
                        # allowed_methods=cdn.AllowedMethods.ALLOW_ALL,
                        viewer_protocol_policy=cdn.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                    ),
                    # domain_names=["example.com"],
                    # certificate=certificate,
                )

            case "prod":
                self.cdn_id = cdn.Distribution(self, prj_name+'-cdn-s3-image-'+config,
                    default_behavior=cdn.BehaviorOptions(
                        origin=origin.S3Origin(bucket),
                        # allowed_methods=cdn.AllowedMethods.ALLOW_ALL,
                        viewer_protocol_policy=cdn.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                    ),
                    # domain_names=["example.com"],
                    # certificate=certificate,
                )

        policy_statment_1 = iam.PolicyStatement(effect=iam.Effect.DENY)
        policy_statment_1.sid="deny-cdn"
        policy_statment_1.add_actions("s3:*")
        policy_statment_1.add_resources(f"{bucket.bucket_arn}/assets/*")
        policy_statment_1.add_canonical_user_principal(origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id)

        policy_statment_2 = iam.PolicyStatement()
        policy_statment_2.sid="allow-cdn"
        policy_statment_2.effect.ALLOW
        policy_statment_2.add_actions("s3:GetObject")
        policy_statment_2.add_resources(f"{bucket.bucket_arn}/*")
        policy_statment_2.add_canonical_user_principal(origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id)

        policy_document = iam.PolicyDocument()
        policy_document.add_statements(policy_statment_1)
        policy_document.add_statements(policy_statment_2)

        s3.CfnBucketPolicy(self, prj_name+"-s3-policy-"+config,
            bucket=bucket.bucket_name,
            policy_document=policy_document
        )

        self.cdn_output_1 = CfnOutput(self, 'cdn-output',
            value=self.cdn_id.domain_name,
            export_name='cdn-domain-name-'+config
        )

