
import json
import logging
import os
import uuid
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
region = os.environ.get('AWS_REGION', 'ap-southeast-1')
kinesis = boto3.client('kinesis', region)
s3_client = boto3.client('s3', region)
ecs = boto3.client('ecs', region)
max_instances = int(os.environ.get('MAX_INSTANCES', '10'))
projects_per_instance = int(os.environ.get('PROJECTS_PER_INSTANCE', '200'))
input_stream = os.environ.get('INPUT_STREAM')


def process_request(event, context):
    calculation_id = uuid.uuid4().hex
    # download request from s3
    s3 = event['Records'][0]['s3']
    s3_bucket = s3['bucket']['name']
    s3_key = s3['object']['key']
    file_path = f'/tmp/{calculation_id}.json'
    s3_client.download_file(s3_bucket, s3_key, file_path)
    # read the request
    with open(file_path, 'rt') as request_file:
        request_data = json.load(request_file)
    # launch fargate instances
    stream = kinesis.describe_stream(StreamName=input_stream)
    shards = stream['StreamDescription']['Shards']
    instance_count = min(
        [request_data['count'] // projects_per_instance, max_instances])
    projects = request_data['projects']
    hash_keys = []
    results = {'sequence_numbers': [], 'shard_ids': []}
    for i in range(instance_count):
        shard = shards[i]
        hash_key = shard['HashKeyRange']['StartingHashKey']
        hash_keys.append(hash_key)
        response = send_project(
            calculation_id,
            projects[i],
            hash_key
        )
        logger.info(response)
        sequence_number = str(response['SequenceNumber'])
        shard_id = response['ShardId']
        run_calculation(
            calculation_id, input_stream, shard_id, sequence_number
        )

    # post projects into kinesis
    for i in range(instance_count, len(projects)):
        response = send_project(
            calculation_id,
            projects[i],
            hash_keys[i % instance_count]
        )

    return results


def run_calculation(calculation_id, stream_name, shard_id, sequence_number):
    response = ecs.run_task(
        cluster='calculators',
        launchType='FARGATE',
        taskDefinition='calculator:1',
        count=1,
        platformVersion='LATEST',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-5feebc19',
                    'subnet-cf3157a8',
                    'subnet-d2ab3c9b'
                ],
                'securityGroups': [
                    'sg-4a9b2732',
                    'sg-2d574b4b'
                ],
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'calculator',
                    'environment': [
                        {
                            'name': 'SHARD_ID',
                            'value': shard_id
                        },
                        {
                            'name': 'STREAM_NAME',
                            'value': stream_name
                        },
                        {
                            'name': 'START_SEQUENCE_ID',
                            'value': sequence_number
                        },
                        {
                            'name': 'CALCULATION_ID',
                            'value': calculation_id
                        }
                    ],
                },
            ]
        })
    logger.info(response)


def send_project(calculation_id, project, hash_key):
    payload = json.dumps(project)
    response = kinesis.put_record(
        StreamName=input_stream,
        Data=payload,
        PartitionKey=calculation_id,
        ExplicitHashKey=hash_key
    )
    return response


def process_response(event, context):
    logger.info(event)
