import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()


class DynamoDB(object):
    NAME = 'key'
    SESSION_DATA = 'dialog_fields'

    def __init__(self, table_name, endpoint_url=None):
        self._table_name = table_name
        self._dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url=endpoint_url)

    def create_table(self, read_capacity_units=1, write_capacity_units=1):
        logger.debug("**************** entering DynamoDB.create_table")
        table = self._dynamodb.create_table(
            TableName=self._table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'name',
                    'KeyType': 'RANGE'  # Provided to support users in future versions
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': read_capacity_units,
                'WriteCapacityUnits': write_capacity_units
            }
        )


    def get_item(self, user_id, name):
        logger.debug("**************** entering DynamoDB.get_item")
        table = self._dynamodb.Table(self._table_name)
        return_val = None
        try:
            response = table.get_item(
                Key={
                    'id': user_id,
                    'name': name
                }
            )
        except ClientError as e:
            logger.critital(e.response['Error']['Message'])
        else:
            if "Item" in response:
                return_val = response['Item']
        return return_val

    def update_data(self, user_id, name, attribute, value):
        logger.debug("**************** entering DynamoDB.update_data")
        try:
            table = self._dynamodb.Table(self._table_name)
            response = table.update_item(
                Key={
                    'id': user_id,
                    'name': name
                },
                UpdateExpression="set {} = :a".format(attribute),
                ExpressionAttributeValues={
                    ':a': value
                },
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as e:
            logger.critical(e.response['Error']['Message'])
            response = None
        return response

    def query_by_userid(self, user_id):
        logger.debug("**************** entering DynamoDB.query_by_userid")
        items = {}
        try:
            table = self._dynamodb.Table(self._table_name)
            response = table.query(
                KeyConditionExpression=Key('id').eq(user_id)
            )
            items = response['Items']
        except ClientError as e:
            logger.critical("********* Exception in DynamoDB.query_by_userid {}".format(e.response['Error']['Message']))
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.debug("Redirecting: No table found, automatically creating table NOW!!!")
                self.create_table()

        return items

    def delete_item(self, user_id, name):
        logger.debug("**************** entering DynamoDB.delete_item")
        try:
            table = self._dynamodb.Table(self._table_name)
            response = table.delete_item(
                Key={
                    'id': user_id,
                    'name': name
                }
            )
        except ClientError as e:
            logger.critical(e.response['Error']['Message'])
            raise
        else:
            return response

    def load(self, user_id):
        logger.debug("**************** entering DynamoDB.load")
        dialog_data = {}
        persisted_user_data = self.query_by_userid(user_id)

        if len(persisted_user_data) == 0:
            self.update_data(user_id, DynamoDB.NAME, DynamoDB.SESSION_DATA, '{}')
        else:
            user_data = persisted_user_data[0]
            # Replace with json dump
            dialog_data = eval(user_data[DynamoDB.SESSION_DATA])

        return dialog_data

    def save(self, user_id, fields_to_persist, session_data):
        logger.debug("**************** entering DynamoDB.save")
        dialog_dict = {}
        for name in fields_to_persist:
            value = self.get_attribute(session_data, [name])
            if value is not None:
                dialog_dict[name] = {'value': value}

        self.update_data(user_id, DynamoDB.NAME, DynamoDB.SESSION_DATA, str(dialog_dict))

    def get_attribute(self, attributes, path):
        val = attributes
        try:
            for arg in path:
                val = val[arg]
        except KeyError:
            val = None
        return val
