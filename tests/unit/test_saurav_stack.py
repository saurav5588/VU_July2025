import aws_cdk as core
import aws_cdk.assertions as assertions

from saurav.saurav_stack import SauravStack

# example tests. To run these tests, uncomment this file along with the example
# resource in saurav/saurav_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SauravStack(app, "saurav")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
