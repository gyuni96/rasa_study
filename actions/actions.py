from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import SlotSet

class SubmitBookingForm(FormAction):
    def name(self) -> Text:
        return "booking_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["service_type", "name"]

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        service_type = tracker.get_slot("service_type")
        name = tracker.get_slot("name")

        # 여기에 예약 처리 로직을 추가합니다.
        # 예약 처리가 완료되면 메시지를 반환합니다.
        dispatcher.utter_message(template="utter_submit")

        return []