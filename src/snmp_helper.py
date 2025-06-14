import subprocess
import re

class SNMPHelper:
    # MIB objects can be specified directly as (MIB_NAME, OBJECT_NAME) tuples
    # or as OIDs if a specific MIB is not needed or available.
    OIDS = {
        'Descrição do Sistema': ('SNMPv2-MIB', 'sysDescr', 0),
        'Object ID': ('SNMPv2-MIB', 'sysObjectID', 0),
        'Tempo de Atividade': ('SNMPv2-MIB', 'sysUpTime', 0),
        'Nome SNMP': ('SNMPv2-MIB', 'sysName', 0),
        'Contato': ('SNMPv2-MIB', 'sysContact', 0),
        'Localização': ('SNMPv2-MIB', 'sysLocation', 0),
        'Serviços': ('SNMPv2-MIB', 'sysServices', 0),
        'Número de Interfaces': ('IF-MIB', 'ifNumber', 0),
        # These OIDs might be vendor-specific or require specific MIBs
        # For Net-SNMP defaults, these OIDs usually work without extra MIBs if agent is configured.
        'CPU Idle (%)': '1.3.6.1.4.1.2021.11.11.0', # UCD-SNMP-MIB::ssCpuIdle.0
        'Memória Total (kB)': '1.3.6.1.4.1.2021.4.5.0', # UCD-SNMP-MIB::memTotalReal.0
        'Memória Livre (kB)': '1.3.6.1.4.1.2021.4.6.0', # UCD-SNMP-MIB::memAvailReal.0
    }

    @staticmethod
    def snmp_get(ip, community, oid_or_mib_tuple):
        """
        Executes an SNMP GET request for a specific OID or MIB object from a host.
        Uses pysnmp for MIB resolution.
        """
        try:
            # Determine if it's an OID string or a MIB tuple
            if isinstance(oid_or_mib_tuple, tuple):
                # MIB object: (MIB_NAME, OBJECT_NAME, INDEX)
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(),
                           CommunityData(community),
                           UdpTransportTarget((ip, 161)),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid_or_mib_tuple)))
                )
            else:
                # OID string
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
                    # varBind is a tuple: (ObjectIdentity, value)
                    # We are interested in the value part
                    return str(varBind[1])
        except Exception:
            return None

    @classmethod
    def get_all_info(cls, ip, community='public'):
        """
        Collects all SNMP information defined in OIDS for a given host.
        """
        info = {}
        for desc, oid_data in cls.OIDS.items():
            value = cls.snmp_get(ip, community, oid_data)
            if value:
                info[desc] = value
        return info
# import subprocess
# import re
#
# class SNMPHelper:
#     # Dicionário de OIDs SNMP comuns com suas descrições amigáveis.
#     OIDS = {
#         'Descrição do Sistema': '1.3.6.1.2.1.1.1.0',
#         'Object ID': '1.3.6.1.2.1.1.2.0',
#         'Tempo de Atividade': '1.3.6.1.2.1.1.3.0',
#         'Nome SNMP': '1.3.6.1.2.1.1.5.0',
#         'Contato': '1.3.6.1.2.1.1.4.0',
#         'Localização': '1.3.6.1.2.1.1.1.6.0', # Corrigido: '1.3.6.1.2.1.1.6.0' (era 1.3.6.1.2.1.1.1.6.0)
#         'Serviços': '1.3.6.1.2.1.1.7.0',
#         'Número de Interfaces': '1.3.6.1.2.1.2.1.0',
#         'CPU Idle (%)': '1.3.6.1.4.1.2021.11.11.0', # OID para uso de CPU em alguns sistemas (Net-SNMP)
#         'Memória Total (kB)': '1.3.6.1.4.1.2021.4.5.0', # OID para memória total (Net-SNMP)
#         'Memória Livre (kB)': '1.3.6.1.4.1.2021.4.6.0', # OID para memória livre (Net-SNMP)
#     }
#
#     @staticmethod
#     def snmp_get(ip, community, oid):
#         """
#         Executa um comando snmpget para recuperar o valor de um OID específico de um host.
#         Requer que o 'snmpget' esteja instalado e disponível no PATH do sistema.
#         """
#         try:
#             # Executa o comando snmpget
#             result = subprocess.check_output(
#                 ['snmpget', '-v1', '-c', community, ip, oid],
#                 stderr=subprocess.STDOUT # Redireciona o erro padrão para a saída padrão
#             ).decode(errors='ignore') # Decodifica a saída, ignorando erros
#
#             # Tenta extrair o valor da saída do snmpget
#             match = re.search(r'=\s+\w+:\s+(.+)', result)
#             if match:
#                 return match.group(1).strip() # Retorna o valor limpo
#             return result.strip() # Retorna a saída bruta se não houver correspondência
#         except Exception:
#             return None # Retorna None em caso de erro (ex: host não responde SNMP, OID não existe)
#
#     @classmethod
#     def get_all_info(cls, ip, community='public'):
#         """
#         Tenta coletar todas as informações SNMP definidas em OIDS para um determinado host.
#         A comunidade SNMP padrão é 'public'.
#         """
#         info = {}
#         for desc, oid in cls.OIDS.items():
#             value = cls.snmp_get(ip, community, oid)
#             if value:
#                 info[desc] = value # Armazena o valor se for obtido com sucesso
#         return info