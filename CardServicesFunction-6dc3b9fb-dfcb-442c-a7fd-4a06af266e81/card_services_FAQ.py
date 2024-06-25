import dialogstate_utils as dialog
import traceback

def handler(intent_request):
    try:
        intent = dialog.get_intent(intent_request)
        active_contexts = dialog.get_active_contexts(intent_request)
        session_attributes = dialog.get_session_attributes(intent_request)
        
        answer = intent_request['requestAttributes']['x-amz-lex:kendra-search-response-question_answer-answer-1']
        del intent['kendraResponse']

        return dialog.close(active_contexts, session_attributes, intent, 
                            [{'contentType': 'PlainText', 'content': answer}])
    except:
        print(traceback.format_exc())
        return dialog.close(active_contexts, session_attributes, intent, 
                            [{'contentType': 'PlainText', 'content': "I don't know that"}])