"""
Standard util methods to manage dialog state
"""

import traceback
import boto3
import json
from boto3.dynamodb.conditions import Key, Attr

def close(active_contexts, session_attributes, intent, messages):
    intent['state'] = 'Fulfilled'
    return {
        'sessionState': {
            'activeContexts': active_contexts,
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent
        },
        'requestAttributes': {},
        'messages': messages
    }
    

def elicit_intent(active_contexts, session_attributes, intent, messages):
    intent['state'] = 'Fulfilled'
    
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ElicitIntent'
    session_attributes['previous_slot_to_elicit'] = None
    
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'activeContexts': active_contexts,
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            "state": "Fulfilled"
        },
        'requestAttributes': {},
        'messages': messages
    }

def elicit_slot(slotToElicit, active_contexts, session_attributes, intent, messages):
    intent['state'] = 'InProgress'
    
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ElicitSlot'
    session_attributes['previous_slot_to_elicit'] = slotToElicit
    
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'activeContexts': active_contexts,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slotToElicit
            },
            'intent': intent
        },
        'requestAttributes': {},
        'messages': messages
    }

def confirm_intent(active_contexts, session_attributes, intent, messages, **previous_state):
    del intent['state']
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ConfirmIntent'
    session_attributes['previous_slot_to_elicit'] = None
    if previous_state:
        session_attributes['previous_dialog_action_type'] = previous_state.get('previous_dialog_action_type')
        session_attributes['previous_slot_to_elicit'] = previous_state.get('previous_slot_to_elicit')
    return {
            'sessionState': {
                'activeContexts': active_contexts,
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'ConfirmIntent'
                },
                'intent': intent
            },
            'requestAttributes': {},
            'messages': messages
        }

def delegate(active_contexts, session_attributes, intent):
    return {
        'sessionState': {
            'activeContexts': active_contexts,
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate'
            },
            'intent': intent,
            'state': 'ReadyForFulfillment'
        },
        'requestAttributes': {}
    }


def get_intent(intent_request):
    interpretations = intent_request['interpretations'];
    if len(interpretations) > 0:
        return interpretations[0]['intent']
    else:
        return None;

# Look for interpretedValue first. If not go for originalValue
def get_slot(slotname, intent):
    try:
        return intent['slots'][slotname]['value']['interpretedValue']
    except:
        try:
            return intent['slots'][slotname]['value']['originalValue']
        except:
            return None
    
def set_slot(slotname, slotvalue, intent):
    if slotvalue == None:
        intent['slots'][slotname] = None
    else:
        intent['slots'][slotname] = {
                "value": {
                "interpretedValue": slotvalue,
                "originalValue": slotvalue,
                "resolvedValues": [
                    slotvalue
                ]
            }
        }

def get_multi_valued_slot(slotname, intent):
    try:
        values = intent['slots'][slotname]['values']
        if not values:
            return None
        slot_values = [item['value']['interpretedValue'] for item in values]
        return slot_values
    except:
        try:
            return intent['slots'][slotname]['value']['originalValue']
        except:
            return None
            
def get_multi_valued_slot_originalvalue(slotname, intent):
    try:
        values = intent['slots'][slotname]['values']
        if not values:
            return None
        original_slot_values = [item['value']['originalValue'] for item in values]
        return original_slot_values
    except:
        try:
            return intent.get['slots'][slotname]['value']['originalValue']
        except:
            return None

    
def got_stuck(previous_state, current_state):
    if not current_state or not previous_state:
        return False
    
    if previous_state['dialogAction'] == current_state['type'] and \
            previous_state['slotToElicit'] == current_state['slotToElicit']:
        return True
    return False
    
def get_active_contexts(intent_request):
    try:
        return intent_request['sessionState'].get('activeContexts')
    except:
        return []

def get_context_attribute(active_contexts, context_name, attribute_name):
    try:
        context = list(filter(lambda x: x.get('name') == context_name, active_contexts))
        return context[0]['contextAttributes'].get(attribute_name)
    except Exception:
        print(traceback.format_exc())
        return None

def get_session_attributes(intent_request):
    try:
        return intent_request['sessionState']['sessionAttributes']
    except:
        return {}

def get_session_attribute(intent_request, session_attribute):
    try:
        return intent_request['sessionState']['sessionAttributes'].get(session_attribute)
    except:
        return None
        
def set_session_attribute(intent_request, session_attribute, value):
    try:
        if intent_request['sessionState'].get('sessionAttributes'):
            intent_request['sessionState']['sessionAttributes'][session_attribute] = value
        else:
            intent_request['sessionState']['sessionAttributes'] = {}
            intent_request['sessionState']['sessionAttributes'][session_attribute] = value
        return intent_request
            
    except:    
        return intent_request

def set_active_contexts(intent_request, context_name, context_attributes, time_to_live, turns_to_live):
    try:
        active_contexts = intent_request.get('sessionState')['activeContexts']
        if not active_contexts:
            intent_request.get('sessionState')['activeContexts'] = []
    except KeyError:
        print(traceback.format_exc())
        intent_request.get('sessionState')['activeContexts'] = []
        active_contexts = intent_request.get('sessionState')['activeContexts']
    except Exception:
        print(traceback.format_exc())
        return []
    finally:
        active_contexts.append({
            'name': context_name,
            'contextAttributes': context_attributes,
            "timeToLive": {
                "timeToLiveInSeconds": time_to_live,
                "turnsToLive": turns_to_live
            }
        })
        intent_request.get('sessionState')['activeContexts'] = active_contexts
    
def persist_dialog_state(dialog_state, bot_id, bot_alias_id, session_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('state_cache')
    table.put_item(
       Item={
            'session_id': session_id,
            'dialog_state': dialog_state,
            'bot_id': bot_id,
            'bot_alias_id': bot_alias_id
        }
    )
    return 

def get_interpreted_intents(intent_request):
    try:
        intents = [{'name':intents_list['intent']['name'], 'nluConfidence':intents_list.get('nluConfidence')}  
                        for intents_list in intent_request['interpretations']]
        return intents
    except:
        return []

def get_previous_slot_to_elicit(intent_request):
    session_attributes = get_session_attributes(intent_request)
    if session_attributes: return session_attributes.get('previous_slot_to_elicit')
    return None
        