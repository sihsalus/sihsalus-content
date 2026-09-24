import json
import unittest
from profile_startup import container_metrics, thread_metrics

class ProfilePrivacy(unittest.TestCase):
    def test_container_identity_and_unknown_values_are_not_emitted(self):
        data = {"Name": "synthetic-private", "CPUPerc": "199.12%", "MemPerc": "80.01%", "PIDs": "57"}
        self.assertEqual(container_metrics(json.dumps(data)),
                         {"cpu_percent": 199.12, "memory_percent": 80.01, "processes_and_threads": 57})
        for key in ("CPUPerc", "MemPerc", "PIDs"):
            data[key] = "synthetic-private"
        self.assertEqual(container_metrics(json.dumps(data)), {})
        for invalid in ('{"CPUPerc":"NaN%","MemPerc":"1000%"}', 'null', '[]', 'private'):
            self.assertEqual(container_metrics(invalid), {})

    def test_only_fixed_categories_and_states_survive(self):
        sample = '''"synthetic-private-thread" #15
   java.lang.Thread.State: RUNNABLE
        at org.hibernate.event.internal.DefaultFlushEntityEventListener.onFlushEntity(Private.java:123)
        at org.openmrs.module.initializer.api.loc.LocationsCsvParser.save(Private.java:12)
"synthetic-private-background" #16
   java.lang.Thread.State: WAITING
        at java.lang.Object.wait(Private.java:123)
'''
        result = thread_metrics(sample)
        self.assertEqual(result, [{"state": "RUNNABLE", "stack_categories": ["hibernate_dirty_check", "initializer_locations"]}])
        self.assertNotIn("private", json.dumps(result).lower())
        self.assertNotIn("123", json.dumps(result))

    def test_unknown_state_and_frames_are_not_emitted(self):
        sample = '''"synthetic-private" #1
   java.lang.Thread.State: PRIVATE
        at org.openmrs.module.initializer.api.PrivateValue(Secret.java:1)
'''
        self.assertEqual(thread_metrics(sample), [{"state": None, "stack_categories": []}])

if __name__ == '__main__':
    unittest.main()
