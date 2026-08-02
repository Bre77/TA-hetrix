import os
import sys
import json
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunk_input_runtime.modularinput import Argument, Event, EventWriter, Scheme, Script


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
        # Get Variables
        input_name, input_items = inputs.inputs.popitem()
        kind, name = input_name.split("://")
        checkpointfile = os.path.join(
            self._input_definition.metadata["checkpoint_dir"], name
        )

        # Password Encryption
        secrets = self.context.credentials.protect_input_fields(
            kind=kind,
            stanza=name,
            values=input_items,
            fields=("key",),
            placeholder=self.MASK,
        )
        auth = {"key": secrets["key"]}

        # Checkpoint
        try:
            with open(checkpointfile, "r") as f:
                checkpoints = json.load(f)
        except:
            checkpoints = {}

        # Get Data
        with requests.get(
            f"https://api.hetrixtools.com/v1/{auth['key']}/uptime/monitors/0/5000/"
        ) as r:
            if not r.ok:
                ew.log(EventWriter.ERROR, f"Failed to get data from Hetrix: {r.text}")
                return
            for monitor in r.json()[0]:
                if monitor["Last_Check"] > checkpoints.get(monitor["ID"], 0):
                    # Remove the API Report Link since it contains the API key
                    monitor["Report_Links"].pop("API_Report_Link")
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
