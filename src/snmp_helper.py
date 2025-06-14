import subprocess
import re
from pysnmp.hlapi import *

class SNMPHelper:
    OIDS = {
        'Descrição do Sistema': ('SNMPv2-MIB', 'sysDescr', 0),
        'Object ID': ('SNMPv2-MIB', 'sysObjectID', 0),
        'Tempo de Atividade': ('SNMPv2-MIB', 'sysUpTime', 0),
        'Nome SNMP': ('SNMPv2-MIB', 'sysName', 0),
        'Contato': ('SNMPv2-MIB', 'sysContact', 0),
        'Localização': ('SNMPv2-MIB', 'sysLocation', 0),
        'Serviços': ('SNMPv2-MIB', 'sysServices', 0),
        'Número de Interfaces': ('IF-MIB', 'ifNumber', 0),
        'CPU Idle (%)': '1.3.6.1.4.1.2021.11.11.0',
        'Memória Total (kB)': '1.3.6.1.4.1.2021.4.5.0',
        'Memória Livre (kB)': '1.3.6.1.4.1.2021.4.6.0',
    }

    @staticmethod
    def snmp_get(ip, community, oid_or_mib_tuple):
        try:
            if isinstance(oid_or_mib_tuple, tuple):
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