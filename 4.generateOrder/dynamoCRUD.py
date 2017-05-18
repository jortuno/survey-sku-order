'''

QUERY and PUT dynamodb data 

'''
from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

def scanMeta(table, fe, pe, ean):
	table = dynamodb.Table(table)
	response = table.scan(
		FilterExpression=fe,
		ProjectionExpression=pe,
		ExpressionAttributeNames=ean
		)
	return response
	
def queryMeta(table, pe, ean, kce):
	table = dynamodb.Table(table)
	response = table.query(
	ProjectionExpression = pe,
	ExpressionAttributeNames= ean, 
	KeyConditionExpression = kce
	)	
	return response
	
def queryMetaIndex(table,kce,i):
	table = dynamodb.Table(table)
	response = table.query(
	IndexName= i,
	KeyConditionExpression = kce
	)	
	return response

def putItem(table,item):
	table = dynamodb.Table(table)
	response = table.put_item(Item=item)
	return response
	
def updateItem(table,key,update,expression):
	table = dynamodb.Table(table)
	response = table.update_item(Key=key,
		UpdateExpression=update,
		ExpressionAttributeValues=expression,
		ReturnValues="UPDATED_NEW"
		)
	return response
