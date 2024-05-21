from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import Restarted, SlotSet, SessionStarted, ActionExecuted, EventType
from rasa_sdk.events import FollowupAction, ActiveLoop
from rasa_sdk.events import UserUtteranceReverted, ConversationPaused
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Dict, List, Text, Optional
import re, json
from utils.Database import Database
from config.DatabaseConfig import DatabaseConfig
import requests
import time
import logging

global db_conn
def db_conn():
    global db_conn
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME = DatabaseConfig()
    db_conn = Database(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    db_conn.connect()
    print(db_conn)

db_conn()

logger = logging.getLogger(__name__)
## 로그
class ActionHelloWorld(Action):
    def name(self) -> str:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        logger.info("ActionHelloWorld is triggered.")
        
        user_name = tracker.get_slot('user_name')
        if user_name:
            response = f"Hello {user_name}!"
            logger.info(f"Greeted user: {user_name}")
        else:
            response = "Hello stranger!"
            logger.info("Greeted an unknown user.")
        
        dispatcher.utter_message(text=response)
        return [SlotSet("greet_response", response)]

# 세션 재시작 액션 클래스
class ActionRestarted(Action):

    def name(self) -> Text:
        return "action_restart"

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('ActionRestarted')
        print(Restarted())
        return [Restarted()]

# 서비스 요청 완료 액션 클래스
class ActionReserve(Action):

    def name(self):
        return "action_reserve"

    def run(self, dispatcher, tracker, domain):
        print('ActionReserve self', self)
        metadata = tracker.latest_message.get('metadata', {})
        accessToken = metadata.get('accessToken')
        print('ActionReserve dispatcher', dispatcher.messages)
        print('ActionReserve tracker', tracker.slots)
        print('ActionReserve metadata', metadata)
        print('ActionReserve accessToken', accessToken)
        # print('ActionGowithCheckTermination domain', domain)
        first_message = tracker.events[0]
        # 최초 메시지의 인텐트 확인
        first_intent = None
        # for message in tracker.events:
        #     print('message', message)
        #     if 'parse_data' in message:
        #         intent = message['parse_data']['intent']['name']
        #         print('intent ', intent)
        if 'parse_data' in first_message:
            first_intent = first_message['parse_data']['intent']['name']

        print('first_message', first_message)
        print('first_intent ', first_intent)

        print(f'실행 확인용')

        headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': accessToken}
        data = tracker.slots

        # 테스트용임
        res = requests.post('http://localhost:7077/common/test', data=json.dumps(data), headers=headers)

        # res = requests.post('http://localhost:8010/api/use/post/reserve', data=json.dumps(data), headers=headers)
        # print(f"{res.status_code} | {res.text}")
        # your business logic here
        # should_terminate = check_for_termination(<params>)

        # if should_terminate:
        #     return [FollowupAction("action_listen")]
        return [Restarted()]
        # return [FollowupAction("action_listen")]

# 세션 시작 액션 클래스
class ActionSessionStart(Action):

    def name(self) -> Text:
        return "action_session_start"

    @staticmethod
    def fetch_slots(tracker: Tracker) -> List[EventType]:
        slots = []
        print('fetch_slots', tracker)
        for key in ('service_type', 'userName', 'start_date', 'end_date', 'departure', 'destination'):
            value = tracker.get_slot(key)
            print('fetch_slots key : %s, value : %s' % (key, value))
        #     if value is not None:
        #         slots.append(SlotSet(key=key, value=value))
        # return slots
    async def run(self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # the session should begin with a `session_started` event
        events = [SessionStarted()]
        metadata = tracker.get_slot('session_started_metadata')

        # Do something with the metadata
        print('meatadata', metadata)
        # any slots that should be carried over shold come after the `session_started` event
        # events.extend(self.fetch_slots(tracker))

        # an `action_listen` should be added at the end as a user manage follows
        events.append(ActionExecuted('action_listen'))
        print('events', events)
        return events


class ActionDefaultFallback(Action):
    """Executes the fallback action and goes back to the previous state of the dialogue"""

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_default")
        # itb_answer_failed_mgmt insert
        # 공백 문자는 무시?
        print('action_default_fallback slots', tracker.slots)
        # Revert user message which led to fallback.
        # return [ConversationPaused(), UserUtteranceReverted()]

# 서비스 요청 중단 액션 클래스
class ActionDeactiveLoop(Action):

    def name(self) -> Text:
        return "action_deactive_loop"

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('ActionDeactiveLoop ', tracker.slots)
        dispatcher.utter_message(template="utter_stop_booking")
        return [Restarted()]

# 안내 서비스 액션 클래스
class ActionInt00004(Action):
    def name(self) -> Text:
        return "action_int00004"
    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('tracker.sender_id:', tracker.sender_id)
        compCd = tracker.latest_message.get('metadata', {}).get('compCd', '')
        print('compCd: ', compCd)
        print(tracker.latest_message)

        # user_events = [event for event in tracker.events if event['event'] == 'user']
        # print(user_events)
        # for message in tracker.events:
        #     print('message', message)
        #     if 'parse_data' in message:
        #         intent = message['parse_data']['intent']['name']
        #         print('intent ', intent)
        # if 'parse_data' in first_message:
        #     first_intent = first_message['parse_data']['intent']['name']

        # dispatcher.utter_message(response="utter_int00004_message")
        intent = tracker.get_intent_of_latest_message()
        sql = (
            f"select /* replace(answer_phrase, '\n\n', '\r') as */ answer_phrase"
            f"  from mosimi_chat.itb_answer_mgmt"
            f" where intent_id='{intent}'"
            f"   and comp_cd='{compCd}'"
        )
        answer_result = db_conn.select_one(sql)
        dispatcher.utter_message(text=answer_result['answer_phrase'])

        # 임시
        # intents = {'int00005': '동행 서비스', 'int00006': '돌봄 서비스'}
        detail_sql = (
            f"select iir.child_intent_id, iim.intent_nm"
            f"  from mosimi_chat.itb_intent_relation iir"
            f"  join mosimi_chat.itb_intent_mgmt iim"
            f"    on iir.child_intent_id = iim.intent_id"
            f" where iir.parent_intent_id='{intent}'"
            f"   and iir.comp_cd='{compCd}'"
        )
        print(intent)
        relation_result = db_conn.select_all(detail_sql)
        buttons = []
        if len(relation_result) > 0:
            for relation in relation_result:
                payload = f"/{relation['child_intent_id']}"
                buttons.append({"title": "{}".format(relation['intent_nm']), "payload": payload})

            dispatcher.utter_message(text='다음과 같은 서비스들이 있습니다.', buttons=buttons)

class ValidateInt00001Form(FormValidationAction):
    def name(self) -> Text:
        return "validate_int00001_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        print('ValidateInt00001Form Service', tracker.get_slot('Service'))
        print('ValidateInt00001Form slots_mapped_in_domain', slots_mapped_in_domain)
        return slots_mapped_in_domain

    async def run(
            self,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[EventType]:
        extraction_events = await self.extract_custom_slots(dispatcher, tracker, domain)
        tracker.add_slots(extraction_events)
        print('ValidateInt00001Form run extraction_events ', extraction_events)
        latest_intent = tracker.latest_message['intent'].get('name')
        print(latest_intent)
        validation_events = await self.validate(dispatcher, tracker, domain)
        tracker.add_slots(validation_events)
        print('ValidateInt00001Form run validation_events ', validation_events)


        next_slot = await self.next_requested_slot(dispatcher, tracker, domain)
        print('ValidateInt00001Form run next_slot ', next_slot)

        if next_slot:
            validation_events.append(next_slot)

        return validation_events

    # 서비스 타입 validation
    async def validate_Service(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print('ValidateInt00001Form validate_Service ', value)
        latest_intent = tracker.latest_message['intent'].get('name')
        if value.find('/') != -1:
            value = value.replace('/', '')
            value = value.replace(latest_intent, '')
            value_json = json.loads(value)
            value = value_json['Service']
        print(latest_intent)
        print(value)
        print('latest_message intent ', latest_intent)
        return {"Service": value}

# 서비스 요청하기 검증 액션 클래스
class ValidateInt00002Form(FormValidationAction):
    def name(self) -> Text:
        return "validate_int00002_form"

    # 필수 요청 슬롯 설정
    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        compCd = tracker.latest_message.get('metadata', {}).get('compCd', '')
        print('ValidateInt00002Form compCd: ', compCd)
        print('ValidateInt00002Form required_slots Service', tracker.get_slot('Service'))
        print('ValidateInt00002Form required_slots current_slot_values', tracker.current_slot_values())
        service = tracker.get_slot('Service')
        print('ValidateInt00002Form required_slots slots_mapped_in_domain', slots_mapped_in_domain)
        # print('ValidateInt00002Form domain', domain)
        print('ValidateInt00002Form required_slots slots[service]', domain['slots']['Service']['values'])
        # 돌봄 서비스는 출발지 슬롯을 필수 슬롯에서 제외
        # if tracker.get_slot('serviceType') == '돌봄':
        #     slots_mapped_in_domain.remove('departure')
        # print('slots_mapped_in_domain', slots_mapped_in_domain)
        # if service is not None and service
        return slots_mapped_in_domain

    # 서비스 타입 validation
    async def validate_Service(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print('ValidateInt00002Form validate_Service ', value)
        print('ValidateInt00002Form validate_Service current_slot_values', tracker.current_slot_values())
        latest_intent = tracker.latest_message['intent'].get('name')
        if value.find('/') != -1:
            value = value.replace('/', '')
            value = value.replace(latest_intent, '')
            value_json = json.loads(value)
            value = value_json['Service']
            print(value)

        if value is None:
            dispatcher.utter_message('동행 또는 돌봄과 함께 다시 입력해주세요.')
        else:
            return {"Service": value}
        
    async def validate_service_detail_for_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        
        print("#######################################################")

        """Validate service_detail_for_int00002 slot value."""
        if slot_value not in ["One Day(9시간)", "기타동행", "한시간전용(1시간)", "정기검진", "외래진료", "투석전용(5시간)"]:
            dispatcher.utter_message(text="잘못된 서비스 선택입니다. 다시 선택해주세요.")
            return {"service_detail_for_int00002": None}
        return {"service_detail_for_int00002": slot_value}

    # 이용자명 validation
    async def validate_Name(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print('ValidateInt00002Form validate_Name ', value)
        return {"Name": value}

    # 서비스 시작일자 validation
    async def validate_StartDate(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # 날짜 형식에 일치하지 않으면 메시지 출력 후 슬롯 값 초기화
        if not self.check_date_format(value):
            dispatcher.utter_message(text="날짜 형식이 아닙니다.\nex) 2024-03-21")
            return {"StartDate": None}

        return {"StartDate": value}

    # 서비스 종료일자 validation
    def validate_EndDate(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if not self.check_date_format(value):
            dispatcher.utter_message(text="날짜 형식이 아닙니다.\nex) 2024-03-21")
            return {"EndDate": None}

        return {"EndDate": value}

    # 날짜 포맷 검증
    def check_date_format(self, date) -> bool:
        replace_value = re.sub('[^0-9]', '', date)  # 숫자 이외 문자 제거
        print('check_date_format origin value ', date)
        print('check_date_format origin value ', replace_value)
        match = re.match("(19|20)\d{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])", replace_value)  # replace_value가 YYYYMMDD에 일치하는지 검사
        print(match)
        # 일치 여부가 있으면 True, 없으면 False
        return match is not None

    # 서비스 출발지 validation
    def validate_Departure(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"Departure": value}

    # 서비스 도착지 validation
    def validate_Destination(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"Destination": value}

# 서비스 요청하기 검증 액션 클래스
class Validateint00003Form(FormValidationAction):
    def name(self) -> Text:
        return "validate_int00003_form"

    # 필수 요청 슬롯 설정
    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        compCd = tracker.latest_message.get('metadata', {}).get('compCd', '')
        print('Validateint00003Form compCd: ', compCd)
        print('Validateint00003Form Service', tracker.get_slot('Service'))
        print('Validateint00003Form slots_mapped_in_domain', slots_mapped_in_domain)
        # 돌봄 서비스는 출발지 슬롯을 필수 슬롯에서 제외
        # if tracker.get_slot('serviceType') == '돌봄':
        #     slots_mapped_in_domain.remove('departure')
        # print('slots_mapped_in_domain', slots_mapped_in_domain)
        return slots_mapped_in_domain

    # 서비스 타입 validation
    async def validate_Service(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print('Validateint00003Form validate_Service ', value)
        # print('Validateint00003Form validate_Service domain ', domain)
        # if value is None:
        #     dispatcher.utter_message('동행 또는 돌봄과 함께 다시 입력해주세요.')
        # else:
        return {"Service": value}
    # 이용자명 validation
    async def validate_Name(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print('validate_Name ', value)
        return {"Name": value}

    # 서비스 시작일자 validation
    async def validate_StartDate(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # 날짜 형식에 일치하지 않으면 메시지 출력 후 슬롯 값 초기화
        if not self.check_date_format(value):
            dispatcher.utter_message(text="날짜 형식이 아닙니다.\nex) 2024-03-21")
            return {"StartDate": None}

        return {"StartDate": value}

    # 서비스 종료일자 validation
    def validate_EndDate(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if not self.check_date_format(value):
            dispatcher.utter_message(text="날짜 형식이 아닙니다.\nex) 2024-03-21")
            return {"EndDate": None}

        return {"EndDate": value}

    # 날짜 포맷 검증
    def check_date_format(self, date) -> bool:
        replace_value = re.sub('[^0-9]', '', date)  # 숫자 이외 문자 제거
        print('check_date_format origin value ', date)
        print('check_date_format origin value ', replace_value)
        match = re.match("(19|20)\d{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])", replace_value)  # replace_value가 YYYYMMDD에 일치하는지 검사
        print(match)
        # 일치 여부가 있으면 True, 없으면 False
        return match is not None

    # 서비스 출발지 validation
    def validate_Departure(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"Departure": value}

    # 서비스 도착지 validation
    def validate_Destination(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"Destination": value}