from aws_cdk import (
    Stack, Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cw,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cwa,
    aws_dynamodb as ddb,
)
from constructs import Construct
import os


class SauravStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---- URLs to monitor
        URLS = ["https://www.python.org", "https://www.github.com"]

        # ---- Canary Lambda
        canary_fn = _lambda.Function(
            self, "CanaryFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="canary.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda_src")),
            timeout=Duration.seconds(15),
            environment={"CW_NAMESPACE": "WebHealth", "URLS": ",".join(URLS)},
        )

        # allow Canary to publish custom metrics
        canary_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        # run every 5 minutes
        events.Rule(
            self, "CanarySchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(canary_fn)],
        )

        # ---- Dashboard
        dashboard = cw.Dashboard(self, "WebHealthDashboard", dashboard_name="WebHealth")

        avail_metrics = [
            cw.Metric(
                namespace="WebHealth",
                metric_name="Availability",
                dimensions_map={"URL": u},
                statistic="avg",
                period=Duration.minutes(5),
            )
            for u in URLS
        ]
        lat_metrics = [
            cw.Metric(
                namespace="WebHealth",
                metric_name="Latency",
                dimensions_map={"URL": u},
                statistic="avg",
                period=Duration.minutes(5),
            )
            for u in URLS
        ]

        dashboard.add_widgets(
            cw.GraphWidget(
                title="Availability (0–1 avg)",
                left=avail_metrics,
                left_y_axis=cw.YAxisProps(min=0, max=1),
            )
        )
        dashboard.add_widgets(
            cw.GraphWidget(title="Latency (s avg)", left=lat_metrics)
        )

        # ---------- STEP 3: SNS + DynamoDB + Logger Lambda + Alarms ----------
        # SNS topic + email
        topic = sns.Topic(self, "WebHealthAlerts", display_name="WebHealth Alerts")
        topic.add_subscription(subs.EmailSubscription("sauravgiri3137@gmail.com"))

        # DynamoDB table
        table = ddb.Table(
            self, "AlarmLogTable",
            partition_key=ddb.Attribute(name="alarmEventId", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
        )

        # Logger Lambda (SNS -> Lambda -> DynamoDB)
        logger_fn = _lambda.Function(
            self, "AlarmLoggerFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda_src")),
            timeout=Duration.seconds(15),
            environment={"TABLE_NAME": table.table_name},
        )
        table.grant_write_data(logger_fn)
        topic.add_subscription(subs.LambdaSubscription(logger_fn))

        # Alarms per URL
        for u in URLS:
            avail_metric = cw.Metric(
                namespace="WebHealth",
                metric_name="Availability",
                dimensions_map={"URL": u},
                statistic="avg",
                period=Duration.minutes(5),
            )
            lat_metric = cw.Metric(
                namespace="WebHealth",
                metric_name="Latency",
                dimensions_map={"URL": u},
                statistic="avg",
                period=Duration.minutes(5),
            )

            a_avail = cw.Alarm(
                self, f"AvailLow{u.replace('https://', '').replace('.', '').replace('/', '')}",
                metric=avail_metric,
                threshold=0.99,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            )

            a_lat = cw.Alarm(
                self, f"LatencyHigh{u.replace('https://', '').replace('.', '').replace('/', '')}",
                metric=lat_metric,
                threshold=0.20,  # seconds
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            )

            for a in (a_avail, a_lat):
                a.add_alarm_action(cwa.SnsAction(topic))
                a.add_ok_action(cwa.SnsAction(topic))
