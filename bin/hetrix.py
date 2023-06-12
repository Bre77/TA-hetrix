import os
import sys
import json
import requests
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.modularinput import *


class Input(Script):
    MASK = "<encrypted>"
    APP = "TA-hetrix"

    def get_scheme(self):
        scheme = Scheme("Hetrix")
        scheme.description = "Pull Hetrix data"
        scheme.use_external_validation = False
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            Argument(
                name="key",
                title="API Key",
                data_type=Argument.data_type_string,
                required_on_create=True,
                required_on_edit=False,
            )
        )

        return scheme

    def stream_events(self, inputs, ew):
        self.service.namespace["app"] = self.APP
        # Get Variables
        input_name, input_items = inputs.inputs.popitem()
        kind, name = input_name.split("://")
        checkpointfile = os.path.join(
            self._input_definition.metadata["checkpoint_dir"], name
        )

        # Password Encryption
        auth = {}
        updates = {}

        for item in ["key"]:
            stored_password = [
                x
                for x in self.service.storage_passwords
                if x.username == item and x.realm == name
            ]
            if input_items[item] == self.MASK:
                if len(stored_password) != 1:
                    ew.log(
                        EventWriter.ERROR,
                        f"Encrypted {item} was not found for {input_name}, reconfigure its value.",
                    )
                    return
                auth[item] = stored_password[0].content.clear_password
            else:
                if stored_password:
                    ew.log(EventWriter.DEBUG, "Removing Current password")
                    self.service.storage_passwords.delete(username=item, realm=name)
                ew.log(EventWriter.DEBUG, "Storing password and updating Input")
                self.service.storage_passwords.create(input_items[item], item, name)
                updates[item] = self.MASK
                auth[item] = input_items[item]
        if updates:
            self.service.inputs.__getitem__((name, kind)).update(**updates)

        KEY = auth["key"]

        # Checkpoint
        try:
            with open(checkpointfile, "r") as f:
                checkpoints = json.load(f)
        except:
            checkpoints = {}

        # Get Data
        with requests.get(
            f"https://api.hetrixtools.com/v1/{KEY}/uptime/monitors/0/5000/"
        ) as r:
            if not r.ok:
                ew.log(EventWriter.ERROR, f"Failed to get data from Hetrix: {r.text}")
                return
            for monitor in r.json()[0]:
                if monitor["Last_Check"] > checkpoints.get(monitor["ID"], 0):
                    ew.write_event(
                        Event(
                            data=json.dumps(monitor, separators=(",", ":")),
                            source=input_name,
                            sourcetype="hetrix:monitors",
                            time=monitor["Last_Check"],
                        )
                    )
                    checkpoints[monitor["ID"]] = monitor["Last_Check"]
                else:
                    ew.log(
                        EventWriter.DEBUG,
                        f"Skipping  {monitor['ID']} since it hasnt been checked since last time",
                    )

        with open(checkpointfile, "w") as f:
            json.dump(checkpoints, f)


if __name__ == "__main__":
    exitcode = Input().run(sys.argv)
    sys.exit(exitcode)
