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
import logging
import datetime

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


## 풀백 액션 클래스
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

        # 메시지 json_string으로 변환
        json_string = json.dumps([answer_result['answer_phrase']], ensure_ascii=False, indent=4)

        dispatcher.utter_message(custom={ "text": json_string})

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

class TokenVerificationForService(Action):
    def name(self) -> Text:
        ## 액션 이름 정의
        return "action_token_verification_for_service"
    
    def run (
            self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # 토큰정보 metadata에서 추출
        auth_token = tracker.latest_message.get('metadata', {}).get('Authorization', '')

        if auth_token :
            # 토큰이 있는경우 - 서비스 묻기
            # dispatcher.utter_message(response="utter_ask_serviceCd_int00001")
            return [FollowupAction("int00001_form")] # 폼을 바로 시작

        else :
            # 토큰이 없는경우
            dispatcher.utter_message(custom = { "text" : json.dumps(["서비스 요청을 위해서는 로그인이 필요합니다.\n로그인 후 다시 시도해주세요."])})

class ValidateInt00001Form(FormValidationAction):
    def name(self) -> Text:
        return "validate_int00001_form"

    def validate_serviceCd_int00001(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 설정")
        print("slot_value : ", slot_value)
        return {"serviceCd_int00001": slot_value}
    

class ActionFetchUserList(Action):

    def name(self) -> Text:
        return "action_fetch_user_list"

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # 토큰정보 metadata에서 추출
        Authorization = tracker.latest_message.get('metadata', {}).get('Authorization', '')
        
        serivceCd = tracker.get_slot('serviceCd_int00002') if tracker.get_slot('serviceCd_int00002') != '' else tracker.get_slot('service_int00003')
        service = 'int00002' if serivceCd == 'SV10' else 'int00003'

        if Authorization :
            
            # 토큰이 있는경우 - 유저 정보를 가져온다.
            url = "http://localhost:8010/api/use/get/chatbot/user"
            headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': Authorization}
            data = {"intent" : service}

            response = requests.api.post(url, data=json.dumps(data) , headers=headers)
            user_list = response.json()

            if user_list :
                dispatcher.utter_message(custom={ "text" : json.dumps(['이용하실 고객님을 선택해주세요.']) , "BUTTON" : user_list})
            else :
                dispatcher.utter_message(response="utter_ask_ServiceDetail")
        else :
            # 토큰이 없는경우
            dispatcher.utter_message(custom = { "text" : json.dumps(["서비스 요청을 위해서는 로그인이 필요합니다.\n로그인 후 다시 시도해주세요."])})
    

class ActionSetUserInfo(Action): 
    def name(self) -> Text:
        return "action_set_user_info"
    
    def run(
            self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        )-> List[Dict[Text, Any]]:

            print("############################사용자 정보 설정")
            
            serivceCd = tracker.get_slot('serviceCd_int00002') if tracker.get_slot('serviceCd_int00002') != '' else tracker.get_slot('service_int00003')
            service = 'int00002' if serivceCd == 'SV10' else 'int00003'
            
            userSysId = tracker.get_slot('userSysId_' + service)
            Authorization = tracker.latest_message.get('metadata', {}).get('Authorization', '')

            if userSysId != 'new' and Authorization :

                response = requests.api.post("http://localhost:8010/api/use/get/chatbot/user/"+userSysId, headers={'Authorization': Authorization})
                user_info = response.json()
                return [
                    SlotSet("userNm_" + service, user_info["userNm"]),
                    SlotSet("userBirthDate_" + service , user_info["userBirthdate"]),
                    SlotSet("userGenderCd_" + service , user_info["userGenderCd"]),
                    SlotSet("userPhoneNo_" + service , user_info["userPhoneNo"]),
                    SlotSet("memberRelationCd_" + service , user_info["memberRelateionCd"]),
                    FollowupAction(service + "_form") # 폼을 바로 시작
                ]
            else : 
                return [
                    FollowupAction(service + "_form") # 폼을 바로 시작
                ]  

# class ActionSeviceDetail(Action):
#     def name(self) -> Text:
#         return "action_service_detail"
    
#     def run (
#             self, 
#             dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]
#         )-> List[Dict[Text, Any]]:
#             dispatcher.utter_message(custom = { "text" : json.dumps(["서비스 상세 정보를 입력해주세요."]) , "BUTTON" : [{'title' : '외진' , 'payload' : '/inform{"ServiceDetail" : "외진"}'}, {'title' : '외진' , 'payload' : '/inform{"ServiceDetail" : "외진"}'}]})

#             return []
#             # FollowupAction("int00002_form") # 폼을 바로 시작

# 서비스 요청하기 검증 액션 클래스
class ValidateInt00002Form(FormValidationAction):
    def name(self) -> Text:
        return "validate_int00002_form"

    def validate_userSysId_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # 사용자 정보가 없을경우 어떻게 들어오는지도 확인해야됨
        print("##############################이용자 시스템 정보 설정")
        return {"userSysId_int00002": slot_value}
    
    def validate_serviceCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 설정")
        return {"serviceCd_int00002": slot_value}
    
    def validate_serviceDtlCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 상세 정보 설정")
        return {"serviceDtlCd_int00002": slot_value}

    def validate_userNm_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################이용자명 설정")
        return {"userNm_int00002": slot_value}
    
    def validate_userBirthDate_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################이용자 생년월일 설정")
        
        try : 
            userBirthDate = slot_value.replace("-", "")

            valid_date = datetime.datetime.strptime(userBirthDate, "%Y%m%d")
            return {"userBirthDate_int00002": userBirthDate}
        except ValueError:
            dispatcher.utter_message(custom = { "text" : json.dumps(["날짜 형식이 아닙니다.\nex) 2024-03-21 또는 20240321"])})
            return {"userBirthDate_int00002": None}

    def validate_userPhoneNo_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################이용자 전화번호 설정")
        
        userPhoneNo = slot_value.replace("-", "")

        # 전화번호 형식 검사 (예: 10자리 또는 11자리 숫자)
        phone_pattern = re.compile(r"^\d{10,11}$")
        if phone_pattern.match(userPhoneNo):

            formatted_phone_no = self.format_phone_no(userPhoneNo)

            return {"userPhoneNo_int00002": formatted_phone_no}
        else:
            dispatcher.utter_message(custom= {"text" : json.dumps(["전화번호 형식이 아닙니다.\nex) 01012345678"])})
            return {"userPhoneNo_int00002": None}
    
    @staticmethod
    def format_phone_no(phone_no: str) -> str:
        """전화번호를 하이픈 포함 형식으로 변환."""
        if len(phone_no) == 10:
            return f"{phone_no[:3]}-{phone_no[3:6]}-{phone_no[6:]}"
        elif len(phone_no) == 11:
            return f"{phone_no[:3]}-{phone_no[3:7]}-{phone_no[7:]}"
        return phone_no

    def validate_userGenderCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################이용자 성별 설정")
        return {"userGenderCd_int00002": slot_value}

    def validate_memberRelationCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################가족관계 설정")
        return {"memberRelationCd_int00002": slot_value}

    def validate_serviceStartDate_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 시작일자 설정")
        return {"serviceStartDate_int00002": slot_value}
    
    def validate_serviceUseTimeCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 시간 설정")
        return {"serviceUseTimeCd_int00002": slot_value}
    
    def validate_serviceStartTime_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################서비스 시작 시간 설정")
        return {"serviceStartTime_int00002": slot_value}
    
    def validate_departAddr_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################출발지 설정")

        buldMnnm = tracker.latest_message.get('metadata', {}).get('buldMnnm', '')
        buldSlno = tracker.latest_message.get('metadata', {}).get('buldSlno', '')
        admCd = tracker.latest_message.get('metadata', {}).get('admCd', '')
        rnMgtSn = tracker.latest_message.get('metadata', {}).get('rnMgtSn', '')
        udrtYn = tracker.latest_message.get('metadata', {}).get('udrtYn', '')

        if buldMnnm == '' or buldSlno == '' or admCd == '' or rnMgtSn == '' or udrtYn == '' :
            dispatcher.utter_message(custom = { "text" : json.dumps(["주소 정보가 없습니다.\n다시 입력해주세요."])})
            return {"departAddr_int00002": None}
        else :
            return {
                "departAddr_int00002": slot_value ,
                "buldMnnm_int00002" :buldMnnm ,
                "buldSlno_int00002" :buldSlno ,
                "departAdmCd_int00002" :admCd ,
                "rnMgtSn_int00002" :rnMgtSn ,
                "udrtYn_int00002" : udrtYn
                }
    
    def validate_departAddrDtl_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################출발지 상세 설정")

        return {"departAddrDtl_int00002": slot_value}


    def validate_destAddr_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################도착지 설정")

        admCd = tracker.latest_message.get('metadata', {}).get('admCd', '')

        return {"destAddr_int00002": slot_value , "destAdmCd_int00002" : admCd}

    def validate_destAddrDtl_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################도착지 상세 설정")

        return {"destAddrDtl_int00002": slot_value}


    def validate_reserveYn_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################예약 여부 설정")
        if slot_value.lower() in ["예", "네", "y", "yes"]:
            return {"reserveYn_int00002": slot_value, "reserveDate_int00002": None, "reserveTime_int00002": None}
        else:
            return {"reserveYn_int00002": slot_value, "reserveDate_int00002": None, "reserveTime_int00002": None}

    def validate_reserveDate_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("##############################예약 날짜 설정")
        reserve_yn = tracker.get_slot("reserveYn_int00002")
        if reserve_yn and reserve_yn.lower() in ["예", "네", "y", "yes"]:
            return {"reserveDate_int00002": slot_value}
        else:
            return {"reserveDate_int00002": None}

    def validate_reserveTime_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("###############################예약 시간 설정")
        reserve_yn = tracker.get_slot("reserveYn_int00002")
        if reserve_yn and reserve_yn.lower() in ["예", "네", "y", "yes"]:
            return {"reserveTime_int00002": slot_value}
        else:
            return {"reserveTime_int00002": None}
        
    def validate_userHealthYn_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("###############################건강상태 유무 설정")
        if slot_value.lower() in ["예", "네", "y", "yes"]:
            return {"userHealthYn_int00002": slot_value, "userHealthCd_int00002": None}
        else:
            return {"userHealthYn_int00002": slot_value, "userHealthCd_int00002": None}

    def validate_userHealthCd_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("###############################건강상태 설정")
        userHealthYn = tracker.get_slot("userHealthYn_int00002")
        if userHealthYn and userHealthYn.lower() in ["예", "네", "y", "yes"]:
            return {"userHealthCd_int00002": slot_value}
        else:
            return {"userHealthCd_int00002": None}

    def validate_requestContentYn_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("###############################요청사항 유무 설정")
        if slot_value.lower() in ["예", "네", "y", "yes"]:
            return {"requestContentYn_int00002": slot_value, "requestContent_int00002": None}
        else:
            return {"requestContentYn_int00002": slot_value, "requestContent_int00002": None}

    def validate_requestContent_int00002(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("###############################요청사항 설정")
        requestContentYn = tracker.get_slot("requestContentYn_int00002")
        if requestContentYn and requestContentYn.lower() in ["예", "네", "y", "yes"]:
            return {"requestContent_int00002": slot_value}
        else:
            return {"requestContent_int00002": None}


    # 필수 요청 슬롯 설정
    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Optional[List[Text]]:
        
        if tracker.get_slot('userHealthYn_int00002') in ['아니요', 'N'] :
            # 건강상태가 없는 경우 userHealthCd 슬롯을 제거
            if 'userHealthCd_int00002' in slots_mapped_in_domain:
                slots_mapped_in_domain.remove('userHealthCd_int00002')
        if tracker.get_slot('requestContentYn_int00002') in ['아니요', 'N'] :
            # 요청사항이 없는 경우 requestContent 슬롯을 제거
            if 'requestContent_int00002' in slots_mapped_in_domain:
                slots_mapped_in_domain.remove('requestContent_int00002')
        if tracker.get_slot('reserveYn_int00002') in ['아니요', 'N'] :
            # 예약이 없는 경우 reserveDate와 reserveTime 슬롯을 제거
            if 'reserveDate_int00002' in slots_mapped_in_domain:
                slots_mapped_in_domain.remove('reserveDate_int00002')
            if 'reserveTime_int00002' in slots_mapped_in_domain:
                slots_mapped_in_domain.remove('reserveTime_int00002')
   
        return slots_mapped_in_domain

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

class ActionPriceCheck(Action):
    def name(self) -> Text:
        return "action_price_check"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        metadata = tracker.latest_message.get('metadata', {})
        Authorization = metadata.get('Authorization')
        compCd = metadata.get('compCd')

        serivceCd = tracker.get_slot('serviceCd_int00002') if tracker.get_slot('serviceCd_int00002') != '' else tracker.get_slot('service_int00003')
        service = 'int00002' if serivceCd == 'SV10' else 'int00003'




# 서비스 요청 완료 액션 클래스
class ActionReserve(Action):

    def name(self):
        return "action_reserve"

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        metadata = tracker.latest_message.get('metadata', {})
        Authorization = metadata.get('Authorization')
        compCd = metadata.get('compCd')

        serivceCd = tracker.get_slot('serviceCd_int00002') if tracker.get_slot('serviceCd_int00002') != '' else tracker.get_slot('service_int00003')
        service = 'int00002' if serivceCd == 'SV10' else 'int00003'

        data = tracker.slots

        new_data = {}

        for key , value in data.items():
            new_key = key.replace("_int00002", "")
            new_data[new_key] = value

        new_data['serviceEndDate'] = new_data['serviceStartDate']
        new_data['serviceEndTime'] = '1500'
        new_data['serviceBasicAmount'] = '40000'
        new_data['stndVat'] = 0.1
        new_data['chargeJson'] = [{"chargeCd": "CH10", "chargeAmount": new_data['serviceBasicAmount']}]

        print("data : " , new_data)

        # 테스트용임
        url = "http://localhost:8010/api/use/post/chatbot/service"
        headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': Authorization}
        response = requests.api.post(url, data=json.dumps(new_data) , headers=headers)
        result = response.text

        # if result == 'Y' :
        #     sql = (
        #         f"select answer_phrase"
        #         f"  from mosimi_chat.itb_answer_mgmt"
        #         f" where intent_id='{intentId}'"
        #         f"   and comp_cd='{compCd}'"
        #      )

        #     answer_result = db_conn.select_one(sql)
            
        #     dispatcher.utter_message(custom ={"text" : "['" + answer_result['answer_phrase'] + "']" })

        # else : 
        #     dispatcher.utter_message(custom ={"text" : "['예약이 실패하였습니다.']" })

        dispatcher.utter_message(custom ={"text" : "['예약이 완료되었습니다.']" })

        return [Restarted()]    