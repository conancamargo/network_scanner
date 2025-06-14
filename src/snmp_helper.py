import json
from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import os

class SNMPHelper:
    # Path to the OIDS configuration file
    OIDS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'snmp_oids.json')
    OIDS = {} # Initialize as empty, will be loaded

    def __init__(self):
        # Load OIDS from the configuration file when an instance is created
        # Or, for a static class, load once
        if not SNMPHelper.OIDS: # Load only if not already loaded
            self._load_oids_from_config()

    @classmethod
    def _load_oids_from_config(cls):
        """Loads OIDs from the external JSON configuration file."""
        try:
            with open(cls.OIDS_CONFIG_FILE, 'r') as f:
                loaded_oids = json.load(f)
                # Convert lists back to tuples for MIB definitions if necessary,
                # though pysnmp.ObjectIdentity usually handles lists for MIB objects fine.
                cls.OIDS = {
                    key: tuple(value) if isinstance(value, list) and len(value) == 3 and isinstance(value[0], str) else value
                    for key, value in loaded_oids.items()
                }
            print(f"OIDs loaded from {cls.OIDS_CONFIG_FILE}")
        except FileNotFoundError:
            print(f"Error: OIDS configuration file not found at {cls.OIDS_CONFIG_FILE}. Using default (empty) OIDS.")
            cls.OIDS = {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {cls.OIDS_CONFIG_FILE}. Check file format.")
            cls.OIDS = {}
        except Exception as e:
            print(f"An unexpected error occurred while loading OIDs: {e}")
            cls.OIDS = {}

    # Ensure OIDs are loaded when the module is imported or class is accessed statically
    # This approach ensures OIDs are loaded even if no instance is created.
    _load_oids_from_config.__is_classmethod = True # Trick to call as class method directly
    if not OIDS: # Load only once during module import
        _load_oids_from_config(SNMPHelper)


    @staticmethod
    def snmp_get(ip, community, oid_or_mib_tuple):
        try:
            if isinstance(oid_or_mib_tuple, (tuple, list)): # Accept both tuple and list for MIB
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(),
                           CommunityData(community),
                           UdpTransportTarget((ip, 161)),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid_or_mib_tuple)))
                )
            else: # Must be a string OID
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
        except Exception: # Broad exception, consider refining
            return None

    @classmethod
    def get_all_info(cls, ip, community='public'):
        info = {}
        for desc, oid_data in cls.OIDS.items():
            value = cls.snmp_get(ip, community, oid_data)
            if value:
                info[desc] = value
        return info