import os, sys
sys.path.append(os.getcwd())
import json
from utils.Database import Database
from config.DatabaseConfig import DatabaseConfig
import os
print(os.getcwd())
print(os.path.dirname(os.path.realpath(__file__)))

global db_conn
def generate_nlu_yaml_text(intent_examples):
    nlu_text = "version: '2.0'\n\nnlu:\n"
    for intent, examples in intent_examples.items():
        nlu_text += f"- intent: {intent}\n"
        nlu_text += "  examples: |\n"
        for example in examples:
            nlu_text += f"    - {example}\n"
    return nlu_text
# 사용자 의도와 예제들
intent_examples = {
    "greet": ["hello", "hi", "hey"],
    "goodbye": ["goodbye", "see you later"],
    "inform": ["I want to book a flight", "I'd like to make a reservation"]
}
domain_keys = ["intents", "entities", "forms", "slots", "responses"]
domain = {
    "intents": ["int00001", "int00002", "int00003", "serviceType", "userName"],
    "entities": ["serviceType", "userName", "serviceStartDate", "serviceEndDate"
                , "departure", "destination"],
    # "excluded_intents": ["affirm", "deny"],
    "forms": [{"gowith_booking_form":
                   {"required_slots": [
                       {"serviceType": [{"- type": "from_entity"},
                                        {"  entity": "serviceType"}]},
                       {"userName": [{"- type": "from_text"},
                                     {"  not_include": "excludes_intents"}]},
                       {"serviceStartDate": [{"- type": "from_text"},
                                             {"  not_intent": "excluded_intents"}]},
                       {"serviceEndDate": [{"- type": "from_text"},
                                           {"  not_include": "excludes_intents"}]},
                       {"departure": [{"- type": "from_text"},
                                      {"  not_include": "excludes_intents"}]},
                       {"destination": [{"- type": "from_text"},
                                        {"  not_include": "excludes_intents"}]}
                   ]}}
            , {"care_booking_form":  [
                       {"serviceType": [{"- type": "from_entity"},
                                        {"  entity": "serviceType"}]},
                       {"userName": [{"- type": "from_text"},
                                     {"  not_include": "excludes_intents"}]},
                       {"serviceStartDate": [{"- type": "from_text"},
                                             {"  not_intent": "excluded_intents"}]},
                       {"serviceEndDate": [{"- type": "from_text"},
                                           {"  not_include": "excludes_intents"}]},
                       {"destination": [{"- type": "from_text"},
                                        {"  not_include": "excludes_intents"}]}
                   ]}],
    "slots": [
        {"serviceType": [
            {"type": "categorical"},
            {"values": ["- 동행", "- 돌봄"]},
            {"influence_conversation": "false"}
        ]},
        {"userName": [
            {"type": "text"},
            {"influence_conversation": "false"}
        ]},
        {"serviceStartDate": [
            {"type": "text"},
            {"influence_conversation": "false"}
        ]},
        {"serviceEndDate": [
            {"type": "text"},
            {"influence_conversation": "false"}
        ]},
        {"departure": [
            {"type": "text"},
            {"influence_conversation": "false"}
        ]},
        {"destination": [
            {"type": "text"},
            {"influence_conversation": "false"}
        ]}
    ],
    "responses": [
        {"utter_ask_serviceType": [
            {"- text": "서비스 종류를 선택해 주세요."},
            {"  buttons": [
                {"- title": "동행"},
                {"  payload": "/int00002{{'serviceType':'동행'}}"},
                {"- title": "돌봄"},
                {"  payload": "/int00003{{'serviceType':'돌봄'}}"}
            ]}
        ]},
        {"utter_ask_userName": [
            {"- text": "이용자명을 입력해주세요."}
        ]},
        {"utter_ask_serviceStartDate": [
            {"- text": "서비스 시작일을 입력해주세요.\n\nex) 2024-03-21"}
        ]},
        {"utter_ask_serviceEndDate": [
            {"- text": "서비스 종료일을 입력해주세요.\n\nex) 2024-03-21"}
        ]},
        {"utter_ask_departure": [
            {"- text": "출발지를 입력해주세요."}
        ]},
        {"utter_ask_destination": [
            {"- text": "도착지를 입력해주세요."}
        ]},
        {"utter_gowith_booking_complete": [
            {"- text": "서비스 요청이 완료 됐습니다.\n- 서비스명: {serviceType}\n- 이용자명: {userName}\n- 서비스 시작일: {serviceStartDate}\n- 서비스 종료일: {serviceEndDate}\n- 출발지: {departure}\n- 도착지: {destination}\n"}
        ]},
        {"utter_care_booking_complete": [
            {"- text": "서비스 요청이 완료 됐습니다.\n- 서비스명: {serviceType}\n- 이용자명: {userName}\n- 서비스 시작일: {serviceStartDate}\n- 서비스 종료일: {serviceEndDate}\n- 도착지: {destination}\n"}
        ]},
        {"utter_please_rephrase": [
            {"- text": "죄송합니다. 질문을 이해하지 못했습니다. 다시 말씀해 주시겠어요?"}
        ]},
        {"utter_please_rephrase": [
            {"- text": "죄송합니다. 질문을 인식하지 못했습니다. 다시 말씀해 주시겠어요?"}
        ]},
        {"utter_ask_confirm_continue": [
            {"- text": "대화와 무관한 내용이 입력되었습니다. 계속 할까요?"},
            {"  buttons": [
                {"- title": "네"},
                {"  payload": "/yes"},
                {"- title": "아니오"},
                {"  payload": "/no"}
            ]}
        ]},
        {"utter_ask_confirm_stop": [
            {"- text": "그만 할까요?"},
            {"  buttons": [
                {"- title": "네"},
                {"  payload": "/affirm"},
                {"- title": "아니오"},
                {"  payload": "/deny"}
            ]}
        ]},
        {"utter_stop_booking": [
            {"- text": "서비스 요청이 중단되었습니다. 다음에 다시 이용해 주세요."}
        ]}
    ],
    "actions": [
        "action_restart",
      "action_gowith_check_termination",
      "action_care_check_termination",
      "action_session_start",
      "action_deactive_loop",
      "validate_gowith_booking_form",
      "validate_care_booking_form"
    ],
    "session_config": [
        {"session_expiration_time": 60},
        {"carry_over_slots_to_new_session": "true"}
    ]
}
def generate_yaml_file(yaml_text, file_name):
    # NLU YAML 텍스트 생성
    # yaml_text = generate_nlu_yaml_text(intent_examples)

    # JSON 형식의 텍스트로 변환
    # yaml_json = json.dumps({"nlu": yaml_text})
    # # 출력
    # print(yaml_json)
    print(yaml_text)
    with open(file_name, "w", encoding='utf-8') as yml_file:
        yml_file.write(yaml_text)

    print("NLU data generated and saved as 'nlu_data.yml'")

def get_intent_json():
    sql = """
        select intent_id
          from mosimi_chat.itb_intent_mgmt
         order by intent_id
    """
    result = db_conn.select_all(sql)
    intent_json = {}
    if result:
        for intent_row in result:
            examples_sql = (
                f"select intent_id, intent_seq, intent_examples"
                f"  from mosimi_chat.itb_intent_traning"
                f" where intent_id = '{intent_row['intent_id']}'"
            )
            examples_result = db_conn.select_all(examples_sql)
            intent_examples = {
                "greet": ["hello", "hi", "hey"],
                "goodbye": ["goodbye", "see you later"],
                "inform": ["I want to book a flight", "I'd like to make a reservation"]
            }
            if examples_result:
                examples = []
                for examples_row in examples_result:
                    examples.append(examples_row['intent_examples'])
                intent_json[intent_row['intent_id']] = examples

    return intent_json
def generate_domain_yaml_text(domain_json):
    padding = chr(32) * 2                               # 패딩 용도 공백 2문자
    domain_text = "version: '2.0'\n\n"
    intents = domain_json['intents']
    entities = domain_json['entities']
    forms = json.loads(domain_json['forms'])
    slots = json.loads(domain_json['slots'])
    responses = json.loads(domain_json['responses'])
    actions = domain_json['actions']
    session_config = domain_json['session_config']

    domain_text += "intents:\n"                                                             #intents:
    for intent in intents.split(','):                   # int00001,int00002,int00003
        domain_text += f"{padding}- {intent}\n"                                             #  - int00001
    domain_text += "entities:\n"                                                            #entities:
    for entity in entities.split(','):                  # Departure,Destination,EndDate,Name,Service,StartDate
        domain_text += f"{padding}- {entity}\n"                                             #  - service
    domain_text += "forms:\n"                                                               #forms:
    for form in forms:
        key = list(form.keys())[0]                      # 폼 명
        domain_text += f"{padding}{key}:\n"                                                 #  int00001_form:
        form_slots = form.get(key)
        required_slots = form_slots.get('required_slots')
        # required_slots 유무. 있으면 form 아래 required_slots 아래 슬롯들 출력, 없으면 form 아래 슬롯들 출력
        form_slots = required_slots if required_slots else form
        if required_slots:
            domain_text += f"{padding * 2}required_slots:\n"                                #    required_slots:
        for slot in form_slots:
            key = list(slot.keys())[0]                  # 슬롯명
            # required_slots가 있으면 6칸 공백 추가, 없으면 4칸 공백 추가
            domain_text += f"{padding * (3 if required_slots else 2)}{key}:\n"              #      service:
            for slot_item in slot.get(key):             # 슬롯 설정 항목
                for k, v in list(slot_item.items()):
                    # required_slots가 있으면 8칸 공백 추가, 없으면 6칸 공백 추가
                    domain_text += f"{padding * (4 if required_slots else 3)}{k}: {v}\n"    #        - type: from_text
    domain_text += "slots:\n"                                                               #slots:
    for slot in slots:
        key = list(slot.keys())[0]                      # 슬롯명
        domain_text += f"{padding}{key}:\n"                                                 #  service:
        for slot_item in slot.get(key):                 # 슬롯 설정 항목
            for k, v in list(slot_item.items()):
                if k == 'values':                                                           # type: categorical
                    domain_text += f"{padding * 2}values:\n"                                # values:
                    for value in v:
                        domain_text += f"{padding * 3}- {value}\n"                          #    - 동행
                else:
                    domain_text += f"{padding * 2}{k}: {v}\n"                               #    type: text

    domain_text += "responses:\n"                                                           #responses:
    for response in responses:
        key = list(response.keys())[0]
        domain_text += f"{padding}{key}:\n"                                                 #  utter_ask_service:
        for response_item in response.get(key):
            for k, v in list(response_item.items()):
                if type(v) is list:             # buttons(itb_entity_mgmt.event_script)가 있으면
                    domain_text += f"{padding * 3}buttons:\n"
                    for item in v:  # [{title, payload}]
                        for k2, v2 in item.items(): # - title, payload
                            domain_text += f'{padding * 4}{k2}: "{v2}"\n'
                else:
                    if v is None:
                        domain_text += f'{padding * 2}{k}: null\n'                          #    -text: 서비스 종류를 입력해주세요
                    else:
                        domain_text += f'{padding * 2}{k}: "{v}"\n'
    domain_text += "actions:\n"                                                             #actions:
    for action in actions:
        domain_text += f"{padding}- {action}\n"                                             #  - action_restart
    # session_config은 일단 고정
    domain_text += "session_config:\n"
    for config in session_config:                                                           #session_config:
        for k, v in config.items():
            domain_text += f"{padding}{k}: {v}\n"                                           #  session_expiration_time:
    print(domain_text)
    return domain_text
def get_domain_json():
    intents_sql = """
        select group_concat(iim.intent_id) as intents
          from mosimi_chat.itb_intent_mgmt iim
    """
    intents_result = db_conn.select_one(intents_sql)

    # entities, slots
    entities_sql = """
        select group_concat(iem.entity_id) as entities
             , json_arrayagg(json_object(iem.entity_id, json_array(json_object('type', 'text'), json_object('influence_conversation', false)))) as slots
          from mosimi_chat.itb_entity_mgmt iem
    """

    entities_result = db_conn.select_one(entities_sql)
    slots_sql = """
        select json_arrayagg(main.slots) as slots 
          from (
            select iem.entity_id, 
                        json_object(
                            iem.entity_id, 
                            case when iec.entity_id is null then
                                    json_array(
                                        json_object('type', 'text'), json_object('influence_conversation', false)
                                    )
                                else 
                                    json_array(
                                        json_object('type', 'categorical')
                                        , json_object('influence_conversation', false)
                                        , json_object('values', json_arrayagg(iec.entity_word))
                                    )
                                end
                        )
                    as slots
              from mosimi_chat.itb_entity_mgmt iem
              left join mosimi_chat.itb_entity_collection iec
                on iem.entity_id = iec.entity_id
             group by iem.entity_id
         ) main
    """
    slots_result = db_conn.select_one(slots_sql)
    forms_sql = """
        select json_arrayagg(json_object(concat(main.intent_id, '_form'), main.entities)) as forms
          from (
            select iim.intent_id
                 , json_object('required_slots', cast(
                        concat('[', group_concat(
                            json_object(ism.entity_id, json_array(
                                /* itb_entity_collection에 단어가 등록되어있는 슬롯이면 */
                                (case when (select count(*) from mosimi_chat.itb_entity_collection iec where iec.entity_id = ism.entity_id) > 0 then
                                        json_object('- type', 'from_entity', '  entity', ism.entity_id)
                                    else 
                                    json_object('- type', 'from_text')
                                    end
                                )
                            )
                        ) order by ism.intent_id, ism.slot_seq), ']')
                        as json)
                    ) as entities
              from mosimi_chat.itb_intent_mgmt iim
              join mosimi_chat.itb_slot_mapping ism
                on iim.intent_id = ism.intent_id
             group by iim.intent_id
        ) main
    """

    forms_result = db_conn.select_one(forms_sql)

    response_sql = """
        select json_arrayagg(main.responses) as responses
          from (
            /* 슬롯 메시지 */
            select json_object(concat('utter_ask_', main.entity_id), main.slot_prompt) as responses
              from (           
                select isp.entity_id , json_arrayagg(json_object('- text', isp.slot_prompt, '  buttons', json_array(json_object('- title', ifnull(isv.view_cd,'') , '  payload', ifnull(isv.view_script,''))))) as slot_prompt
                  from mosimi_chat.itb_slot_prompt isp
             left join mosimi_chat.itb_slot_view isv on isp.entity_id = isv.entity_id 
              group by isp.entity_id
             ) main
             union
             /* 폼 작성 완료 메시지 */
             select json_object(concat('utter_', iam.intent_id, '_message')
                  , json_array(json_object('- text', iam.answer_phrase, '  buttons', 
                        /* 연계되는 인텐트가 있으면 buttons에 연계 인텐트 추가*/
                        (case when iir.parent_intent_id is not null then 
                            json_arrayagg(json_object('- title', (select iim2.intent_nm 
                                                                  from mosimi_chat.itb_intent_mgmt iim2
                                                                 where iim2.intent_id = iir.child_intent_id)
                                                        , '  payload', concat('/', iir.child_intent_id)))
                            else null end)
                        ))) as responses
               from mosimi_chat.itb_intent_mgmt iim
               join mosimi_chat.itb_answer_mgmt iam  
                 on iim.intent_id = iam.intent_id
               left join mosimi_chat.itb_intent_relation iir
                 on iir.parent_intent_id = iim.intent_id
              group by iam.intent_id
              union
             /* 인식하지 못한 입력에 대한 기본 메시지 */
             select json_object('utter_default', json_arrayagg(json_object('- text', ifm.fallback_prompt))) as 'default_response'
               from mosimi_chat.itb_fallback_mgmt ifm
        ) main
    """
    response_result = db_conn.select_one(response_sql)

    domain_json = {
        'intents': intents_result['intents'],
        'entities': entities_result['entities'],
        'forms': forms_result['forms'],
        'slots': slots_result['slots'],
        'responses': response_result['responses'],
        'actions': ['action_restart',
                    'action_reserve',
                    'action_session_start',
                    'action_deactive_loop',
                    'action_default_fallback',
                    'validate_int00001_form',
                    'validate_int00002_form',
                    'validate_int00003_form',
                    'action_int00004',],
        'session_config': [{"session_expiration_time": 60}, {"carry_over_slots_to_new_session": "true"}]
    }
    print(domain_json)
    return domain_json
def main():
    global db_conn
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME = DatabaseConfig()
    db_conn = Database(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    db_conn.connect()

    nlu_yaml_text = generate_nlu_yaml_text(get_intent_json())
    generate_yaml_file(nlu_yaml_text, 'data/nlu.yml')
    domain_yaml_text = generate_domain_yaml_text(get_domain_json())
    generate_yaml_file(domain_yaml_text, 'domain.yml')

if __name__ == '__main__':
    main()