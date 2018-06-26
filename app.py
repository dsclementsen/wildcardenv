from flask import Flask
from flask import jsonify
from flask_cors import CORS

import yaml
# import simplejson as json

import boto3
from botocore.exceptions import ClientError


app = Flask(__name__)
CORS(app)

BUCKET_NAME = "env.innablr.xyz"

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
    objects = client.list_objects(Bucket=BUCKET_NAME, Prefix='stacks/')
#     for item in client.list_objects(Bucket='env.innablr.xyz', Prefix='stacks/')['Contents']:
#         files.append(item['Key'])
    return jsonify(objects)

@app.route("/api/templates")
def get_templates():
    client = get_client('s3')
    files = {}
    # client.list_objects(Bucket='bucket_name', Prefix='prefix_string')['Contents']
    objects = client.list_objects(Bucket=BUCKET_NAME, Prefix='templates/')

    for item in objects['Contents']:
        # obj = client.get_object(Bucket=bucket, Key=key)
        # j = json.loads(obj['Body'].read())
        print(item)
        common_prefix = 'templates/'
        name = item['Key'][len(common_prefix):]
        if len(name) > 0:
            files[item['Key']] = {
                'key': item['Key'],
                'name': name,
                'modified': item['LastModified'],
            }

    templates = []
    for key, item in files.items():
        object = client.get_object(Bucket=BUCKET_NAME, Key=key)
        item['content'] = object['Body'].read().decode('utf-8')
        templates.append(item)

    return jsonify({'templates': templates})


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

@app.route('/api/templates/<template>/quicklaunch/<stack>')
def launch_from_template(template, stack):

    cloudformation = """
AWSTemplateFormatVersion: '2010-09-09'
Metadata:
  License: Apache-2.0
Description: 'Single EC2 install and run httpd service'
Resources:
  EnvStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3-ap-southeast-2.amazonaws.com/env.innablr.xyz/templates/%s
      TimeoutInMinutes: 4
      Parameters:
        KeyName: davur-innablr-dev
  DnsStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3-ap-southeast-2.amazonaws.com/env.innablr.xyz/templates/env-dns-records.yaml
      Parameters:
        EnvName: %s
        EnvDns: !GetAtt [EnvStack, Outputs.PublicDNS]
        RecordType: CNAME
Outputs:
  Dns:
    Description: DNS entry for new environment
    Value: %s.env.innablr.env
""" % (template, stack, stack)

    client = get_client('cloudformation')
    stack_name = "wildcardenv-%s" % stack
    response = client.create_stack(
           StackName=stack_name,
           TemplateBody=cloudformation,
           #Parameters=parameters_as_array(env.parameters),
        )
    # print(response)

    if 'StackId' in response:
        returnValue = {
            "id": "wildcardenv-%s" % stack,
            "stack_id": response['StackId'],
            "name": stack,
            "parameters": "",
            "stack_id": response['StackId'],
            "status": "CREATE_IN_PROGRESS",
        }
    else:
        {"Error": "Create Failed"}

    return jsonify(returnValue)


# @detail_route(methods=['get', 'post',])
# def launch(self, request, pk=None):
#     env = self.get_object()
#
#     if env.stack_id:
#         return self.refresh(request, pk)
#
#
#     client = get_client('cloudformation')
#     stack_name = "wildcardenv-%s" % env.name
#     response = client.create_stack(
#            StackName=stack_name,
#            TemplateBody=env.template.body,
#            Parameters=parameters_as_array(env.parameters),
#         )
#     print(response)
#
#     if 'StackId' in response:
#         env.stack_id = response['StackId']
#         env.status = 'CREATE_IN_PROGRESS'
#         env.save()
#
#     # return Response({'StackId': 'success'})
#     serializer = serializers.EnvironmentSerializer(env)
#     return Response(serializer.data)





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


# from __future__ import print_function
from google.auth.transport import requests
from google.oauth2 import id_token

# https://blog.codecentric.de/en/2018/04/aws-lambda-authorizer/
def generatePolicy(principalId, effect, methodArn):
    authResponse = {}
    authResponse['principalId'] = principalId

    if effect and methodArn:
        policyDocument = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': 'FirstStatement',
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': methodArn
                }
            ]
        }

        authResponse['policyDocument'] = policyDocument

    return authResponse

def lambda_handler(event, context):
    try:
        # Verify and get information from id_token
        idInformation = id_token.verify_oauth2_token(
            event['authorizationToken'],
            requests.Request(),
            '919361216275-tiobj6ratp5cvt8fie6vga30tkh50tf0.apps.googleusercontent.com')
        print(idInformation)

        # Deny access if the account is not a Google account
        if idInformation['iss'] not in ['accounts.google.com',
            'https://accounts.google.com']:
            return generatePolicy(None, 'Deny', event['methodArn'])

        # Get principalId from idInformation
        principalId = idInformation['sub']

    except ValueError as err:
        # Deny access if the token is invalid
        print(err)
        return generatePolicy(None, 'Deny', event['methodArn'])

    return generatePolicy(principalId, 'Allow', event['methodArn'])
