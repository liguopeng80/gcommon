#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: '2021-04-18'
# author: 'gerror_generator.py'

"""
   Error definition and description.
   This file is automatically generated by gerror_generator.py
   NOTE: DO NOT change this file manually!!!
         Go for gerror_generator_source.py instead."""

from gcommon.error.gerror import GError

error_defines = {
    000000: ('ok', u'操作成功'),

    1000001: ('gen_server_internal', u'操作失败'),
    1000002: ('gen_bad_request', u'请求错误'),
    1000003: ('gen_partial_completed', u'部分操作被完成'),
    1000004: ('gen_permission_denied', u'没有权限'),
    1000005: ('gen_exceed_request_limit', u'时间段内访问次数过多'),
    1000006: ('gen_ip_banned', u'ip被封禁'),
    1000007: ('gen_not_completed_yet', u'操作尚未完成'),
    1000008: ('gen_target_not_found', u'对象不存在'),

    1100001: ('err_user_exists', u'用户名已经存在，无法注册'),
    1100002: ('reg_too_much_reg_in_current_loc', u'当前服务器用户过多，无法注册新用户'),
    1100003: ('err_token_invalid', u'token错误'),
    1100004: ('err_token_expired', u'验证token已过期'),
    1100005: ('err_user_inactive', u'账号已存在但未激活'),
    1100006: ('err_bad_token', u'token无效'),
    1100007: ('err_user_banned', u'用户被禁用'),
    1100008: ('err_user_activated', u'用户已激活'),
    1100009: ('err_user_pending_email_validation', u'用户邮箱未验证'),
    1100101: ('gen_need_authentication', u'用户尚未登录'),
    1100102: ('auth_invalid_user_or_pass', u'用户名或密码错误，登录失败。请检查您的输入是否正确?'),
    1100103: ('auth_too_much_errors', u'该用户登录失败次数过多。为保护帐号安全，屏蔽该用户登录10分钟。请稍后重试'),
    1100104: ('auth_invalid_account_status', u'用户帐号的状态异常'),
    1100105: ('auth_permission_denied', u'无子系统权限'),

    8880001: ('server_too_much_users', u'当前服务器的活跃用户已超出服务器的容量，请等待服务器空闲时重试'),
    8880002: ('server_not_implemented', u'服务器尚未实现此功能'),

    9990001: ('gen_client_version_expired', u'客户端版本太低'),
    9990002: ('gen_config_version_expired', u'配置文件版本太低'),
    9990003: ('gen_protocol_not_supported', u'不支持'),
}


class GErrorCodes(object):
    ok = 0

    gen_server_internal = 1000001
    gen_bad_request = 1000002
    gen_partial_completed = 1000003
    gen_permission_denied = 1000004
    gen_exceed_request_limit = 1000005
    gen_ip_banned = 1000006
    gen_not_completed_yet = 1000007
    gen_target_not_found = 1000008

    err_user_exists = 1100001
    reg_too_much_reg_in_current_loc = 1100002
    err_token_invalid = 1100003
    err_token_expired = 1100004
    err_user_inactive = 1100005
    err_bad_token = 1100006
    err_user_banned = 1100007
    err_user_activated = 1100008
    err_user_pending_email_validation = 1100009
    gen_need_authentication = 1100101
    auth_invalid_user_or_pass = 1100102
    auth_too_much_errors = 1100103
    auth_invalid_account_status = 1100104
    auth_permission_denied = 1100105

    server_too_much_users = 8880001
    server_not_implemented = 8880002

    gen_client_version_expired = 9990001
    gen_config_version_expired = 9990002
    gen_protocol_not_supported = 9990003
    pass


class GErrors(object):
    ok = GError.create(0000000, error_defines)

    gen_server_internal = GError.create(1000001, error_defines)
    gen_bad_request = GError.create(1000002, error_defines)
    gen_partial_completed = GError.create(1000003, error_defines)
    gen_permission_denied = GError.create(1000004, error_defines)
    gen_exceed_request_limit = GError.create(1000005, error_defines)
    gen_ip_banned = GError.create(1000006, error_defines)
    gen_not_completed_yet = GError.create(1000007, error_defines)
    gen_target_not_found = GError.create(1000008, error_defines)

    err_user_exists = GError.create(1100001, error_defines)
    reg_too_much_reg_in_current_loc = GError.create(1100002, error_defines)
    err_token_invalid = GError.create(1100003, error_defines)
    err_token_expired = GError.create(1100004, error_defines)
    err_user_inactive = GError.create(1100005, error_defines)
    err_bad_token = GError.create(1100006, error_defines)
    err_user_banned = GError.create(1100007, error_defines)
    err_user_activated = GError.create(1100008, error_defines)
    err_user_pending_email_validation = GError.create(1100009, error_defines)
    gen_need_authentication = GError.create(1100101, error_defines)
    auth_invalid_user_or_pass = GError.create(1100102, error_defines)
    auth_too_much_errors = GError.create(1100103, error_defines)
    auth_invalid_account_status = GError.create(1100104, error_defines)
    auth_permission_denied = GError.create(1100105, error_defines)

    server_too_much_users = GError.create(8880001, error_defines)
    server_not_implemented = GError.create(8880002, error_defines)

    gen_client_version_expired = GError.create(9990001, error_defines)
    gen_config_version_expired = GError.create(9990002, error_defines)
    gen_protocol_not_supported = GError.create(9990003, error_defines)

    pass
