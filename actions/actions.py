from rasa_sdk import Action, Tracker
from rasa_sdk.events import Restarted
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Dict, List, Text, Optional
from datetime import datetime, timedelta
from rasa_sdk.events import ActionExecutionRejected


class ActionRestarted(Action):

    def name(self) -> Text:
        return "action_restart"

    async def run( self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('Restarted')

        return[Restarted()]

class ActionReturnSenderId(Action):
    def name(self) -> Text:
        return "action_return_sender_id"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # 대화 추적기를 통해 세션 ID 가져오기
        session_id = tracker.sender_id
        
        if session_id == 'default' :

            dispatcher.utter_message(response="utter_login")

            return [Restarted()]
        else : 
        # 세션 ID를 사용하여 원하는 작업 수행
        # 여기에서는 세션 ID를 로그에 출력하는 예시입니다.
            print("현재 세션 ID:", session_id)
            return []

class ActionCheckTermination(Action):
    def name(self):
        return "action_check_termination"

    def run(self, dispatcher, tracker, domain):
        # print('ActionCheckTermination self', self)
        # print('ActionCheckTermination dispatcher', dispatcher.messages)
        # print('ActionCheckTermination tracker', tracker.slots)
        # print('ActionCheckTermination domain', domain)

        serviceType = tracker.get_slot('serviceType')
        userName = tracker.get_slot('userName')
        serviceStartDate = tracker.get_slot('serviceStartDate')
        serviceEndDate = tracker.get_slot('serviceEndDate')
        departure = tracker.get_slot('departure')
        destination = tracker.get_slot('destination')

        result = {
            'serviceType': serviceType,
            'userName': userName,
            'serviceStartDate': serviceStartDate,
            'serviceEndDate': serviceEndDate,
            'departure': departure,
            'destination': destination
        }

        # 템플릿 호출
        dispatcher.utter_message(response="utter_booking_slots_values", json_message=result)

        # 결과값 반환
        return [Restarted()] # 재실행

class ActionCheckInactivity(Action):
    def name(self) -> Text:
        return "action_check_inactivity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # 사용자와의 최근 활동 시간 가져오기
        last_activity_time = tracker.latest_message['timestamp']
        now = datetime.now()
        
        # 일정 시간 동안 사용자와의 상호작용이 없을 경우 대화 종료
        if (now - last_activity_time) > timedelta(minutes=1):
            dispatcher.utter_message(text="오랫동안 대화가 없어 종료됩니다.")
            return [ActionExecutionRejected()]
        
        return []