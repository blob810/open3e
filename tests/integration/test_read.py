import os

import pytest

import tests.util.open3e_cmd_wrapper as open3e_process
from tests.util.json_device_dataset_loader import device_dataset, device_dataset_dict
from tests.util.wait import wait_for


READ_DATASET_FILE = os.path.join(os.path.dirname(__file__), "test_data/read.json")


@pytest.mark.parametrize("ecu, did, expected", device_dataset(READ_DATASET_FILE))
def test_read_cmd_json(ecu, did, expected):
  stdout, stderr = open3e_process.read(ecu, [did])

  assert '' == stderr
  assert expected == stdout.strip()


def test_read_cmd_json_multiple_dids():
  ecu = "0x680"
  dids = [256, 505]

  stdout, stderr = open3e_process.read(ecu, dids)

  assert '' == stderr
  read_dataset = device_dataset_dict(READ_DATASET_FILE)
  assert f"{dids[0]} {read_dataset[ecu][dids[0]]}" == stdout.splitlines()[0]
  assert f"{dids[1]} {read_dataset[ecu][dids[1]]}" == stdout.splitlines()[1]


def test_read_cmd_json_sub_did():
  did = "0x680.256.BusType"

  stdout, stderr = open3e_process.read_with_did_string(did)

  assert '' == stderr
  assert '{"ID": 2, "Text": "CanInternal"}' == stdout.strip()


def test_read_cmd_raw():
  ecu = "0x680"
  did = 256

  stdout, stderr = open3e_process.read_raw(ecu, [did])

  assert '' == stderr
  assert "\"01021f091400fd010109c000020064026500040031323334353637383031323334353637\"" == stdout.strip()


@pytest.mark.parametrize("ecu, did, expected", device_dataset(READ_DATASET_FILE))
def test_read_listen_json(open3e_mqtt_client, ecu, did, expected):
  with open3e_process.listen() as _:
    wait_for(lambda: open3e_mqtt_client.is_open3e_online())

    open3e_mqtt_client.subscribe(ecu, did)
    open3e_mqtt_client.publish_cmd("read-json", ecu, [did])

    wait_for(lambda: open3e_mqtt_client.received_messages_count() == 1)

    assert expected == open3e_mqtt_client.received_message_payload(ecu, did)


def test_read_listen_json_multiple_dids(open3e_mqtt_client):
  ecu = "0x680"
  dids = [256, 507]

  with open3e_process.listen() as _:
    wait_for(lambda: open3e_mqtt_client.is_open3e_online())

    for did in dids:
      open3e_mqtt_client.subscribe(ecu, did)

    open3e_mqtt_client.publish_cmd("read-json", ecu, dids)

    wait_for(lambda: open3e_mqtt_client.received_messages_count() == 2)

    read_dataset = device_dataset_dict(READ_DATASET_FILE)
    assert read_dataset[ecu][dids[0]] == open3e_mqtt_client.received_message_payload(ecu, dids[0])
    assert read_dataset[ecu][dids[1]] == open3e_mqtt_client.received_message_payload(ecu, dids[1])


def test_read_listen_json_sub_did(open3e_mqtt_client):
  ecu = "0x680"
  did = 256
  sud_did = "BusType"
  sub_did_fqn = f"{did}.{sud_did}"

  with open3e_process.listen() as _:
    wait_for(lambda: open3e_mqtt_client.is_open3e_online())

    # TODO: why sub did will be published to sub topic and not sub did topic?
    #open3e_mqtt_client.subscribe(ecu, did, f"/{sud_did}")
    open3e_mqtt_client.subscribe(ecu, did)
    open3e_mqtt_client.publish_cmd("read-json", ecu, [sub_did_fqn])

    wait_for(lambda: open3e_mqtt_client.received_messages_count() == 1)

    # TODO: why sub did will be published to sub topic and not sub did topic?
    #assert '{"ID": 2, "Text": "CanInternal"}' == open3e_mqtt_client.received_message_payload(ecu, did[0], f"/{sud_did}")
    assert '{"ID": 2, "Text": "CanInternal"}' == open3e_mqtt_client.received_message_payload(ecu, did)


def test_read_listen_raw(open3e_mqtt_client):
  ecu = "0x680"
  did = 256

  with open3e_process.listen() as _:
    wait_for(lambda: open3e_mqtt_client.is_open3e_online())

    open3e_mqtt_client.subscribe(ecu, did)
    open3e_mqtt_client.publish_cmd("read-raw", ecu, [did])

    wait_for(lambda: open3e_mqtt_client.received_messages_count() == 1)

    assert "01021f091400fd010109c000020064026500040031323334353637383031323334353637" == open3e_mqtt_client.received_message_payload(ecu, did)


def test_read_listen(open3e_mqtt_client):
  ecu = "0x680"
  did = 256

  with open3e_process.listen() as _:
    wait_for(lambda: open3e_mqtt_client.is_open3e_online())

    open3e_mqtt_client.subscribe(ecu, did, "/#")
    open3e_mqtt_client.publish_cmd("read", ecu, [did])

    wait_for(lambda: open3e_mqtt_client.received_messages_count() == 10)

    assert "1" == open3e_mqtt_client.received_message_payload(ecu, did, "/BusAddress")
    assert "2" == open3e_mqtt_client.received_message_payload(ecu, did, "/BusType/ID")
    assert "1234567801234567" == open3e_mqtt_client.received_message_payload(ecu, did, "/VIN")