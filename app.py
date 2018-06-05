from flask import Flask
from flask import jsonify
from flask_cors import CORS

import boto3
from botocore.exceptions import ClientError


app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Hello World!"

# @app.route("/api")
# def hola():
#     stacks = get_defined_stacks()
#     return jsonify(stacks)

@app.route("/api/stacks/<stack>/stop")
def stop(stack):
    client = get_client('cloudformation')
    try:
        response = client.delete_stack(
            StackName=stack
        )
    except ClientError:
        response = None

    return jsonify(response)



@app.route('/api/stacks/saved')
def get_defined_stacks():
    client = get_client('s3')
    files = []
    # client.list_objects(Bucket='bucket_name', Prefix='prefix_string')['Contents']
    objects = client.list_objects(Bucket='env.innablr.xyz', Prefix='stacks/')
#     for item in client.list_objects(Bucket='env.innablr.xyz', Prefix='stacks/')['Contents']:
#         files.append(item['Key'])
    return jsonify(objects)

@app.route("/api/templates")
def get_templates():
    client = get_client('s3')
    files = []
    # client.list_objects(Bucket='bucket_name', Prefix='prefix_string')['Contents']
    objects = client.list_objects(Bucket='env.innablr.xyz', Prefix='templates/')
#     for item in client.list_objects(Bucket='env.innablr.xyz', Prefix='stacks/')['Contents']:
#         files.append(item['Key'])
    return jsonify(objects)

@app.route('/api/stacks', defaults={'stack': None})
@app.route('/api/stacks/<stack>')
def get_current_stacks(stack=None):
    client = get_client('cloudformation')
    stacks = []
    try:
        if stack is None:
            response = client.describe_stacks()
        else:
            response = client.describe_stacks(StackName=stack) # NextToken='1'
        for stack in response['Stacks']:
            if stack['StackName'][:12] == 'wildcardenv-':
                stacks.append(stack)
    except ClientError as e:
        response = {
            'status': 500,
            'message': "Could not retrieve CloudFormation stacks",
            'exception': str(e.response)
        }

    return jsonify(stacks)


#     def refresh(self, request, pk=None):
#         env = self.get_object()
#         client = get_client('cloudformation')
#         env = Environment.objects.get(pk=pk)
#         stack_name = "wildcardenv-%s" % env.name
#
#         try:
#             response = client.describe_stacks(
#                     StackName=stack_name,
#                     NextToken='1'
#                 )
#         except ClientError:
#             response = None
#
#         if response is None:
#             env.status = "DELETED"
#             env.stack_id = ''
#             env.save()
#         elif 'Stacks' in response and len(response['Stacks']) > 0:
#             print(response)
#             stack = response['Stacks'][0]
#             env.stack_id = stack['StackId']
#             env.status = stack['StackStatus']
#             env.save()
#             print(response)
#
#         serializer = serializers.EnvironmentSerializer(env)
#         return Response(serializer.data)
#


def get_client(client):
    return boto3.client(client)

def parameters_as_array(parameters):
    parameter_array = []
    lines = parameters.splitlines()
    for line in lines:
        pairs = line.split('=')
        if len(pairs) == 2:
            key = pairs.pop(0).strip()
            value = '='.join(pairs).strip()
            parameter_array.append({
                'ParameterKey': key,
                'ParameterValue': value,
            })
    return parameter_array
