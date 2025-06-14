import json
from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import os

class SNMPHelper:
    OIDS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'snmp_oids.json')
    OIDS = {} # Initialize as empty, will be loaded

    # Load OIDs when the class is defined, ensuring it's done only once
    @classmethod
    def _load_oids_from_config(cls):
        try:
            with open(cls.OIDS_CONFIG_FILE, 'r') as f:
                loaded_oids = json.load(f)
                cls.OIDS = {
                    key: tuple(value) if isinstance(value, list) and len(value) == 3 and isinstance(value[0], str) else value
                    for key, value in loaded_oids.items()
                }
            # print(f"OIDs loaded from {cls.OIDS_CONFIG_FILE}") # Keep for debugging if needed
        except FileNotFoundError:
            print(f"Error: OIDS configuration file not found at {cls.OIDS_CONFIG_FILE}. Using default (empty) OIDS.")
            cls.OIDS = {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {cls.OIDS_CONFIG_FILE}. Check file format.")
            cls.OIDS = {}
        except Exception as e:
            print(f"An unexpected error occurred while loading OIDs: {e}")
            cls.OIDS = {}

    # Call the loading method immediately after the class is defined
    _load_oids_from_config()


    @staticmethod
    def snmp_get(ip, community, oid_or_mib_tuple):
        try:
            if isinstance(oid_or_mib_tuple, (tuple, list)):
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(),
                           CommunityData(community),
                           UdpTransportTarget((ip, 161)),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid_or_mib_tuple)))
                )
            else:
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(),
                           CommunityData(community),
                           UdpTransportTarget((ip, 161)),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid_or_mib_tuple)))
                )

            if errorIndication:
                return None
            elif errorStatus:
                return None
            else:
                for varBind in varBinds:
                    return str(varBind[1])
        except Exception:
            return None

    @classmethod
    def get_all_info(cls, ip, community='public'):
        info = {}
        for desc, oid_data in cls.OIDS.items():
            value = cls.snmp_get(ip, community, oid_data)
            if value:
                info[desc] = value
        return info