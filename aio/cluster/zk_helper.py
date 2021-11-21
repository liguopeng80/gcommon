#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-03-09

import logging

from gcommon.aio.cluster.cluster_manager import ClusterManager

logger = logging.getLogger('cluster')


def zk_create_working_node(zk_client, data=None):
    """创建服务节点"""
    node_path, root_path = get_path_to_working_node()

    zk_client.ensure_path(root_path)
    result = zk_client.create(node_path, data, ephemeral=True)

    return result


def zk_create_alive_node(zk_client, data=None):
    server = ClusterManager.server

    alive_root = server.cfg.get('zookeeper.path_alive_apps')

    root_path = alive_root + "/" + server.SERVICE_NAME
    node_path = root_path + "/" + server.unique_server_name

    zk_client.ensure_path(root_path)
    result = zk_client.create(node_path, data, ephemeral=True)

    return result


def zk_delete_working_node(zk_client):
    """删除服务节点"""
    node_path, root_path = get_path_to_working_node()

    zk_client.ensure_path(root_path)
    result = zk_client.delete(node_path, ephemeral=True)

    return result


def get_path_to_working_node():
    """当前服务器的工作节点根目录"""
    server = ClusterManager.server

    root_path = get_path_to_working_server(server.SERVICE_NAME)
    # node_path = os.path.join(root_path, server.unique_server_name)
    node_path = root_path + "/" + server.unique_server_name

    return node_path, root_path


def get_path_to_working_server(service_name):
    """某个服务器的工作节点根目录"""
    server = ClusterManager.server
    working_root = server.cfg.get('zookeeper.path_working_apps')

    if working_root.endswith('/'):
        working_root = working_root[:-1]

    root_path = working_root + "/" + service_name

    return root_path

