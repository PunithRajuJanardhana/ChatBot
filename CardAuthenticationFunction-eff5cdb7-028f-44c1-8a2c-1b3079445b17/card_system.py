import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['dynamodb_tablename']
card = dynamodb.Table(table_name)

def get_customer_id(card_number, zip_code):
    try:
        customers = card.scan(
            FilterExpression=Attr("type").eq('account') and
            Attr("card_number").eq(card_number)
        )
        print('customers: ', customers)
        if len(customers.get('Items')) <= 0:
            return None
        customer_id = customers.get('Items')[0]['customer_id']
        customer_with_zip_code = card.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr("type").eq('customer') and
            Attr("zip_code").eq(zip_code)
        )
        print('customer_with_zip_code: ', customer_with_zip_code)
        if len(customer_with_zip_code.get('Items')) <= 0:
            return None
        return customer_id
    except:
        return None