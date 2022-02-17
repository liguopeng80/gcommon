#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-03-09

import logging

from kazoo.exceptions import NoNodeError

from gcommon.aio.cluster.cluster_manager import ClusterManager
from gcommon.utils.gglobal import Global

logger = logging.getLogger("cluster")


def zk_create_working_node(zk_client, server, data=None):
    """创建服务节点"""
    node_path, root_path = get_path_to_current_working_node(server)

    zk_client.ensure_path(root_path)
    result = zk_client.create(node_path, data, ephemeral=True)

    return result


def zk_create_alive_node(zk_client, data=None):
    """创建在线服务节点（不一定工作）"""
    server = ClusterManager.server

    alive_root = server.cfg.get("service.cluster.path_alive_apps")

    root_path = alive_root + "/" + server.SERVICE_NAME
    node_path = root_path + "/" + server.unique_server_name

    zk_client.ensure_path(root_path)
    result = zk_client.create(node_path, data, ephemeral=True)

    return result


def zk_delete_working_node(zk_client, server):
    """删除服务节点"""
    node_path, root_path = get_path_to_current_working_node(server)

    zk_client.ensure_path(root_path)
    result = zk_client.delete(node_path, ephemeral=True)

    return result


def get_path_to_current_working_node(server):
    """当前服务器的工作节点根目录"""
    root_path = get_path_to_working_service(server.service_name)
    # node_path = os.path.join(root_path, server.unique_server_name)
    node_path = root_path + "/" + server.unique_server_name

    return node_path, root_path


def get_path_to_working_service(service_name):
    """某个服务器的工作节点根目录"""
    working_root = Global.config.get("service.cluster.path_working_apps")

    if working_root.endswith("/"):
        working_root = working_root[:-1]

    root_path = f"{working_root}/{service_name}"
    return root_path


def get_path_to_current_alive_node(server):
    """当前服务器的工作节点根目录"""
    root_path = get_path_to_alive_service(server.service_name)
    # node_path = os.path.join(root_path, server.unique_server_name)
    node_path = root_path + "/" + server.unique_server_name

    return node_path, root_path


def get_path_to_alive_service(service_name):
    """某个服务器的工作节点根目录"""
    alive_root = Global.config.get("service.cluster.path_alive_apps")

    if alive_root.endswith("/"):
        alive_root = alive_root[:-1]

    root_path = f"{alive_root}/{service_name}"
    return root_path


def ensure_path_to_service(zk_client, service_name):
    """创建服务节点需要的根目录"""
    working_path = get_path_to_working_service(service_name)
    alive_path = get_path_to_alive_service(service_name)

    zk_client.ensure_path(working_path)
    zk_client.ensure_path(alive_path)


def get_node_data(zk_client, path, allow_no_node=True):
    """读取一个节点的数据"""
    try:
        data, stat = zk_client.get(path)
    except NoNodeError:
        if allow_no_node:
            return ""
        else:
            raise

    if not data:
        return ""

    return data.decode("utf-8")


def update_node_data(zk_client, path: str, data: str):
    """设置节点数据"""
    zk_client.set(path, data.encode("utf-8"))


def get_node_children(zk_client, path):
    """读取一个节点的子节点"""
    data, stat = zk_client.zk_client(path)
    if not data:
        return ""

    return data.decode("utf-8")
