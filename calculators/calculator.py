import json
import logging
import os
import time
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

input_stream = os.environ.get('STREAM_NAME')
output_stream = os.environ.get('STREAM_NAME')
shard_id = os.environ.get('SHARD_ID')
region = os.environ.get('AWS_REGION', 'ap-southeast-1')
kinesis = boto3.client(
    'kinesis',
    region_name=region
)
dynamodb = boto3.resource('dynamodb', region_name=region)
results_table = dynamodb.Table('dev-calculation-results')
start_sequence_number = os.environ.get('START_SEQUENCE_ID')
calculation_id = os.environ.get('CALCULATION_ID')


def calculate():
    logger.info(shard_id)
    shard_iterator = kinesis.get_shard_iterator(
        StreamName=input_stream,
        ShardId=shard_id,
        ShardIteratorType='AT_SEQUENCE_NUMBER',
        StartingSequenceNumber=start_sequence_number
    )
    records_iterator = shard_iterator['ShardIterator']
    with results_table.batch_writer() as batch:
        while True:
            records = kinesis.get_records(
                ShardIterator=records_iterator,
                Limit=100)
            records_iterator = records['NextShardIterator']
            for record in records['Records']:
                data = record['Data'].decode('utf-8')
                project = json.loads(data)
                result = calculate_project(project)
                batch.put_item(Item=result)

            if not records['Records']:
                break


def calculate_project(project):
    project['results']['BOE'] = {}
    project['results']['CashFlow'] = {}
    boe = project['results']['BOE']
    cashflow = project['results']['CashFlow']

    for year in range(project['start_year'], project['end_year']):
        year = str(year)
        production = project['variables']['Production'][year]
        cost = project['variables']['Cost'][year]
        boe_amount = production * 82.2
        boe[year] = str(boe_amount)
        cashflow[year] = str(boe_amount - cost)

    project['calculation_id'] = calculation_id
    # simulate calculation time
    time.sleep(.1)

    return project


if __name__ == '__main__':
    calculate()
