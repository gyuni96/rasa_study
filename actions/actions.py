from rasa_sdk import Action, Tracker
from rasa_sdk.events import Restarted
from rasa_sdk.events import FollowupAction
from typing import Any, Dict, List, Text, Optional


class ActionRestarted(Action):

    def name(self) -> Text:
        return "action_restart"

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        print('ActionRestarted domain', domain)
        return [Restarted()]

class ActionCheckTermination(Action):

    def name(self):
        return "action_check_termination"

    def run(self, dispatcher, tracker, domain):
        print('ActionCheckTermination self', self)
        print('ActionCheckTermination dispatcher', dispatcher.messages)
        print('ActionCheckTermination tracker', tracker.slots)
        print('ActionCheckTermination domain', domain)
        # your business logic here
        # should_terminate = check_for_termination(<params>)

        # if should_terminate:
        #     return [FollowupAction("action_listen")]

        return [FollowupAction("action_listen")]