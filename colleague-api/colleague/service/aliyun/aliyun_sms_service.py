# -*- coding: utf-8 -*-
import sys
import uuid
import os
import json
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.profile import region_provider
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest

"""
短信业务调用接口示例，版本号：v20170525

Created on 2017-06-12

"""
try:
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:
    pass
except Exception as err:
    raise err

# 注意：不要更改
REGION = "cn-hangzhou"
PRODUCT_NAME = "Dysmsapi"
DOMAIN = "dysmsapi.aliyuncs.com"

acs_client = AcsClient(os.getenv("SMS_KEY"), os.getenv("SMS_SEC"), REGION)
region_provider.add_endpoint(PRODUCT_NAME, REGION, DOMAIN)


def send_sms_code(mobile, code):
    params = json.dumps({"code": code})
    resp = send_sms(uuid.uuid4(), mobile, "我的同事", "SMS_143850045", params)
    result = False
    try:
        logging.info(resp)
        resp = json.loads(resp)
        result = (resp.get('Code') == 'OK')
    except Exception, e:
        logging.info(e)
    return result


def send_sms(business_id, phone_numbers, sign_name, template_code, template_param=None):
    smsRequest = SendSmsRequest.SendSmsRequest()
    # 申请的短信模板编码,必填
    smsRequest.set_TemplateCode(template_code)

    # 短信模板变量参数
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)

    # 设置业务请求流水号，必填。
    smsRequest.set_OutId(business_id)

    # 短信签名
    smsRequest.set_SignName(sign_name)

    # 数据提交方式
    # smsRequest.set_method(MT.POST)

    # 数据提交格式
    # smsRequest.set_accept_format(FT.JSON)

    # 短信发送的号码列表，必填。
    smsRequest.set_PhoneNumbers(phone_numbers)

    # 调用短信发送接口，返回json
    smsResponse = acs_client.do_action_with_exception(smsRequest)

    # TODO 业务处理

    return smsResponse


if __name__ == '__main__':
    __business_id = uuid.uuid1()
    # print(__business_id)
    params = "{\"code\":\"313567\"}"
    # params = u'{"name":"wqb","code":"12345678","address":"bz","phone":"13000000000"}'
    k = send_sms_code("18600754152", "123877")
    print type(k)
    print k
