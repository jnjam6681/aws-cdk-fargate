from aws_cdk import (
    CfnOutput,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    Duration,
    Stack
)
from constructs import Construct

class CloudFrontStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: str, lb: elbv2.ILoadBalancerV2, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        acm_arn="arn:aws:acm:us-east-1:739842833640:certificate/12f1f93a-0627-4a2d-ae24-ce18fb4e4cd8"
        certificate = acm.Certificate.from_certificate_arn(self, "certificate", acm_arn)

        match config:
            case 'dev':
                cache_policy = cloudfront.CachePolicy(self, prj_name+"-cache-policy-dev",
                    cache_policy_name=prj_name+"-"+config,
                    comment="aprilia cache policy",
                    default_ttl=Duration.seconds(2),
                    min_ttl=Duration.seconds(2),
                    max_ttl=Duration.seconds(300),
                    cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                    header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Authorization"),
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                    enable_accept_encoding_gzip=True,
                    enable_accept_encoding_brotli=True
                )

                origin_request_policy = cloudfront.OriginRequestPolicy(self, prj_name+"-origin-request-policy-dev",
                    origin_request_policy_name=prj_name+"-"+config,
                    comment="aprilia origin request policy",
                    cookie_behavior=cloudfront.OriginRequestCookieBehavior.all(),
                    header_behavior=cloudfront.OriginRequestHeaderBehavior.allow_list("Host", "Origin", "Accept", "x-xsrf-token", "Referer", "x-inertia", "x-inertia-version"),
                    query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.all()
                )

                cloudfront_info = cloudfront.Distribution(self, prj_name+"-cloudfrond-dev",
                    default_behavior=cloudfront.BehaviorOptions(
                        origin=origins.LoadBalancerV2Origin(
                            lb,
                            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY
                        ),
                        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                        cache_policy=cache_policy,
                        origin_request_policy=origin_request_policy,
                        allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    ),
                    domain_names=["demo.apriliasrgtthailand.com"],
                    certificate=certificate,
                )

            case 'prod':
                cache_policy = cloudfront.CachePolicy(self, prj_name+"-cache-policy-prod",
                    cache_policy_name=prj_name,
                    # comment="aprilia policy",
                    default_ttl=Duration.seconds(2),
                    min_ttl=Duration.seconds(2),
                    max_ttl=Duration.seconds(300),
                    cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                    header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Authorization"),
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                    enable_accept_encoding_gzip=True,
                    enable_accept_encoding_brotli=True
                )

                origin_request_policy = cloudfront.OriginRequestPolicy(self, prj_name+"-origin-request-policy-prod",
                    origin_request_policy_name=prj_name,
                    # comment="aprilia policy",
                    cookie_behavior=cloudfront.OriginRequestCookieBehavior.all(),
                    header_behavior=cloudfront.OriginRequestHeaderBehavior.allow_list("Host, Origin, Accept"),
                    query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.all()
                )

                cloudfront_info = cloudfront.Distribution(self, prj_name+"-cloudfrond-prod",
                    default_behavior=cloudfront.BehaviorOptions(
                        origin=origins.LoadBalancerV2Origin(
                            lb,
                            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY
                        ),
                        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                        cache_policy=cache_policy,
                        response_headers_policy=origin_request_policy
                    ),
                    # domain_names=["example.com"],
                    # certificate=certificate,
                )

        self.ecs_cloudfront_output_1 = CfnOutput(self, 'ecs-cloudfront-output',
            value=cloudfront_info.domain_name,
            export_name='ecs-cloudfront-output-'+config
        )