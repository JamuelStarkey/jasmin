# Copyright 2012 Fourat Zouari <fourat@gmail.com>
# See LICENSE for details.

import logging
import re
from jasmin.vendor.smpp.pdu.pdu_types import (EsmClass, EsmClassMode, EsmClassType, 
                                RegisteredDelivery, RegisteredDeliveryReceipt, 
                                AddrTon, AddrNpi, 
                                PriorityFlag, ReplaceIfPresentFlag, 
                                DataCoding, DataCodingDefault)
from jasmin.vendor.smpp.pdu.smpp_time import SMPPRelativeTime 
from jasmin.config.tools import ConfigFile

class ConfigUndefinedIdError(Exception):
    """Raised when a *Config class is initialized without ID
    """

class ConfigInvalidIdError(Exception):
    """Raised when a *Config class is initialized with an invalid ID syntax
    """
    
class TypeMismatch(Exception):
    """Raised when a *Config element has not a valid type
    """
    
class UnknownValue(Exception):
    """Raised when a *Config element has a valid type and inappropriate value
    """

# A config map between user-configuration keys and SMPPClientConfig keys.
# user-configuration keys are used to simplify configuration through APIs (jcli)
SMPPClientConfigMap = {'cid': 'id', 'host': 'host', 'port': 'port', 'username': 'username',
                       'password': 'password', 'systype': 'systemType', 'logfile': 'log_file', 'loglevel': 'log_level',
                       'bind_to': 'sessionInitTimerSecs', 'elink_interval': 'enquireLinkTimerSecs', 'trx_to': 'inactivityTimerSecs', 
                       'res_to': 'responseTimerSecs', 'con_loss_retry': 'reconnectOnConnectionLoss', 'con_fail_retry': 'reconnectOnConnectionFailure',
                       'con_loss_delay': 'reconnectOnConnectionLossDelay', 'con_fail_delay': 'reconnectOnConnectionFailureDelay',
                       'pdu_red_to': 'pduReadTimerSecs', 'bind': 'bindOperation', 'bind_ton': 'bind_addr_ton', 'bind_npi': 'bind_addr_npi',
                       'src_ton': 'source_addr_ton', 'src_npi': 'source_addr_npi', 'dst_ton': 'dest_addr_ton', 'dst_npi': 'dest_addr_npi',
                       'addr_range': 'address_range', 'src_addr': 'source_addr', 'esm_class': 'esm_class', 'proto_id': 'protocol_id', 
                       'priority': 'priority_flag', 'validity': 'validity_period', 'dlr': 'registered_delivery', 'ripf': 'replace_if_present_flag',
                       'def_msg_id': 'sm_default_msg_id', 'coding': 'data_coding', 'requeue_delay': 'requeue_delay', 'submit_throughput': 'submit_sm_throughput',
                       'dlr_expiry': 'dlr_expiry'
                       }

class SMPPClientConfig():
    def __init__(self, **kwargs):
        if kwargs.get('id', None) == None:
            raise ConfigUndefinedIdError('SMPPClientConfig must have an id')
        
        idcheck = re.compile(r'^[A-Za-z0-9_-]{3,25}$')
        if idcheck.match(str(kwargs.get('id'))) == None:
            raise ConfigInvalidIdError('SMPPClientConfig id syntax is invalid')
            
        self.id = str(kwargs.get('id'))
        
        self.host = kwargs.get('host', '127.0.0.1')
        if not isinstance(self.host, str):
            raise TypeMismatch('host must be a string')
        self.port = kwargs.get('port', 2775)
        if not isinstance(self.port, int):
            raise TypeMismatch('port must be an integer')
        self.username = kwargs.get('username', 'smppclient')
        self.password = kwargs.get('password', 'password')
        self.systemType = kwargs.get('systemType', '')
        self.log_file = kwargs.get('log_file', '/var/log/jasmin/default-%s.log' % self.id)
        self.log_level = kwargs.get('log_level', logging.INFO)
        self.log_format = kwargs.get('log_format', '%(asctime)s %(levelname)-8s %(process)d %(message)s')
        self.log_date_format = kwargs.get('log_dateformat', '%Y-%m-%d %H:%M:%S')
        
        # Timeout for response to bind request
        self.sessionInitTimerSecs = kwargs.get('sessionInitTimerSecs', 30)
        if not isinstance(self.sessionInitTimerSecs, int) and not isinstance(self.sessionInitTimerSecs, float):
            raise TypeMismatch('sessionInitTimerSecs must be an integer or float')
        
        # Enquire link interval
        self.enquireLinkTimerSecs = kwargs.get('enquireLinkTimerSecs', 10)
        if not isinstance(self.enquireLinkTimerSecs, int) and not isinstance(self.enquireLinkTimerSecs, float):
            raise TypeMismatch('enquireLinkTimerSecs must be an integer or float')
        
        # Maximum time lapse allowed between transactions, after which period
        # of inactivity, the connection is considered as inactive and will reconnect 
        self.inactivityTimerSecs = kwargs.get('inactivityTimerSecs', 300)
        if not isinstance(self.inactivityTimerSecs, int) and not isinstance(self.inactivityTimerSecs, float):
            raise TypeMismatch('inactivityTimerSecs must be an integer or float')
        
        # Timeout for responses to any request PDU
        self.responseTimerSecs = kwargs.get('responseTimerSecs', 60)
        if not isinstance(self.responseTimerSecs, int) and not isinstance(self.responseTimerSecs, float):
            raise TypeMismatch('responseTimerSecs must be an integer or float')
        
        # Reconnection
        self.reconnectOnConnectionLoss = kwargs.get('reconnectOnConnectionLoss', True)
        self.reconnectOnConnectionFailure = kwargs.get('reconnectOnConnectionFailure', True)
        self.reconnectOnConnectionLossDelay = kwargs.get('reconnectOnConnectionLossDelay', 10)        
        if not isinstance(self.reconnectOnConnectionLossDelay, int) and not isinstance(self.reconnectOnConnectionLossDelay, float):
            raise TypeMismatch('reconnectOnConnectionLossDelay must be an integer or float')
        self.reconnectOnConnectionFailureDelay = kwargs.get('reconnectOnConnectionFailureDelay', 10)        
        if not isinstance(self.reconnectOnConnectionFailureDelay, int) and not isinstance(self.reconnectOnConnectionFailureDelay, float):
            raise TypeMismatch('reconnectOnConnectionFailureDelay must be an integer or float')
        
        # Timeout for reading a single PDU, this is the maximum lapse of time between
        # receiving PDU's header and its complete read, if the PDU reading timed out,
        # the connection is considered as 'corrupt' and will reconnect
        self.pduReadTimerSecs = kwargs.get('pduReadTimerSecs', 10)
        if not isinstance(self.pduReadTimerSecs, int) and not isinstance(self.pduReadTimerSecs, float):
            raise TypeMismatch('pduReadTimerSecs must be an integer or float')
        
        self.useSSL = kwargs.get('useSSL', False)
        self.SSLCertificateFile = kwargs.get('SSLCertificateFile', None)
        
        # Type of bind operation, can be one of these:
        # - transceiver
        # - transmitter
        # - receiver
        self.bindOperation = kwargs.get('bindOperation', 'transceiver')
        if self.bindOperation not in ['transceiver', 'transmitter', 'receiver']:
            raise UnknownValue('Invalid bindOperation: %s' % self.bindOperation)
        
        # These are default parameters, c.f. _setConfigParamsInPDU method in SMPPOperationFactory
        self.service_type = kwargs.get('service_type', None)
        self.bind_addr_ton = kwargs.get('bind_addr_ton', AddrTon.UNKNOWN)
        self.bind_addr_npi = kwargs.get('bind_addr_npi', AddrNpi.ISDN)
        self.source_addr_ton = kwargs.get('source_addr_ton', AddrTon.NATIONAL)
        self.source_addr_npi = kwargs.get('source_addr_npi', AddrNpi.ISDN)
        self.dest_addr_ton = kwargs.get('dest_addr_ton', AddrTon.INTERNATIONAL)
        self.dest_addr_npi = kwargs.get('dest_addr_npi', AddrNpi.ISDN)
        self.address_range = kwargs.get('address_range', None)
        self.source_addr = kwargs.get('source_addr', None)
        self.esm_class = kwargs.get('esm_class', EsmClass(EsmClassMode.STORE_AND_FORWARD, EsmClassType.DEFAULT))
        self.protocol_id = kwargs.get('protocol_id', None)
        self.priority_flag = kwargs.get('priority_flag', PriorityFlag.LEVEL_0)
        self.schedule_delivery_time = kwargs.get('schedule_delivery_time', None)
        self.validity_period = kwargs.get('validity_period', None)
        self.registered_delivery = kwargs.get('registered_delivery', RegisteredDelivery(RegisteredDeliveryReceipt.NO_SMSC_DELIVERY_RECEIPT_REQUESTED))
        self.replace_if_present_flag = kwargs.get('replace_if_present_flag', ReplaceIfPresentFlag.DO_NOT_REPLACE)
        self.sm_default_msg_id = kwargs.get('sm_default_msg_id', 0)

        # 5.2.19 data_coding / c. There is no default setting for the data_coding parameter.
        # Possible values:
        # SMSC_DEFAULT_ALPHABET:     0x00 / 0
        # IA5_ASCII:                 0x01 / 1
        # OCTET_UNSPECIFIED:         0x02 / 2
        # LATIN_1:                   0x03 / 3
        # OCTET_UNSPECIFIED_COMMON:  0x04 / 4
        # JIS:                       0x05 / 5
        # CYRILLIC:                  0x06 / 6
        # ISO_8859_8:                0x07 / 7
        # UCS2:                      0x08 / 8
        # PICTOGRAM:                 0x09 / 9
        # ISO_2022_JP:               0x0a / 10
        # EXTENDED_KANJI_JIS:        0x0d / 13
        # KS_C_5601:                 0x0e / 14
        self.data_coding = kwargs.get('data_coding', 0)
        if self.data_coding not in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14]:
            raise UnknownValue('Invalid data_coding: %s' % self.data_coding)

        # These were added to preserve compatibility with smpp.twisted project
        self.addressTon = self.bind_addr_ton
        self.addressNpi = self.bind_addr_npi
        self.addressRange = self.address_range
        
        # QoS
        # Rejected messages are requeued with a fixed delay
        self.requeue_delay = kwargs.get('requeue_delay', 120)
        if not isinstance(self.requeue_delay, int) and not isinstance(self.requeue_delay, float):
            raise TypeMismatch('requeue_delay must be an integer or float')
        self.submit_sm_throughput = kwargs.get('submit_sm_throughput', 1)
        if not isinstance(self.submit_sm_throughput, int) and not isinstance(self.submit_sm_throughput, float):
            raise TypeMismatch('submit_sm_throughput must be an integer or float')
        
        # DLR
        self.dlr_expiry = kwargs.get('dlr_expiry', 86400)
        if not isinstance(self.dlr_expiry, int) and not isinstance(self.dlr_expiry, float):
            raise TypeMismatch('dlr_expiry must be an integer or float')
                
class SMPPClientServiceConfig(ConfigFile):
    def __init__(self, config_file):
        ConfigFile.__init__(self, config_file)
        
        self.log_level = logging.getLevelName(self._get('service-smppclient', 'log_level', 'INFO'))
        self.log_file = self._get('services-smppclient', 'log_file', '/var/log/jasmin/service-smppclient.log')
        self.log_format = self._get('services-smppclient', 'log_format', '%(asctime)s %(levelname)-8s %(process)d %(message)s')
        self.log_date_format = self._get('services-smppclient', 'log_date_format', '%Y-%m-%d %H:%M:%S')
