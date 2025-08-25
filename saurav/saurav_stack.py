from aws_cdk import (
    Stack, Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cw,
    aws_iam as iam
)
from constructs import Construct
import os

class SauravStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        URLS = ["https://www.python.org", "https://www.github.com"]

        canary_fn = _lambda.Function(
            self, "CanaryFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="canary.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda_src")),
            timeout=Duration.seconds(15),
            environment={"CW_NAMESPACE":"WebHealth", "URLS": ",".join(URLS)},
        )

        #  give permission to write metrics
        canary_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # run every 5 minutes
        events.Rule(
            self, "CanarySchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(canary_fn)]
        )

        # Dashboard
        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealth")

        avail_metrics = [cw.Metric(namespace="WebHealth", metric_name="Availability",
                                   dimensions_map={"URL": u}, statistic="avg",
                                   period=Duration.minutes(5)) for u in URLS]
        lat_metrics = [cw.Metric(namespace="WebHealth", metric_name="Latency",
                                 dimensions_map={"URL": u}, statistic="avg",
                                 period=Duration.minutes(5)) for u in URLS]

        dashboard.add_widgets(
            cw.GraphWidget(title="Availability (0–1 avg)", left=avail_metrics,
                           left_y_axis=cw.YAxisProps(min=0, max=1))
        )
        dashboard.add_widgets(
            cw.GraphWidget(title="Latency (s avg)", left=lat_metrics)
        )
