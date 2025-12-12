import logging
from typing import Any

from redis.asyncio import RedisCluster as AsyncRedisCluster
from redis.asyncio import StrictRedis as AsyncStrictRedis
from redis.asyncio.cluster import ClusterNode as AsyncClusterNode

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, startup_nodes: list[dict[str, str | int]], **kwargs: dict[str, Any]) -> None:
        if len(startup_nodes) > 1:
            logger.info("Start async redis with cluster. Cluster nodes: %s", startup_nodes)
            self.redis = AsyncRedisCluster(
                startup_nodes=[
                    AsyncClusterNode(host=node.get("host"), port=node.get("port")) for node in startup_nodes
                ],
            )
        else:
            logger.info("Start async redis without cluster. Redis node: %s", startup_nodes)
            self.redis = AsyncStrictRedis(
                host=startup_nodes[0].get("host"), port=startup_nodes[0].get("port"), decode_responses=True
            )


redis_client = RedisCache(startup_nodes=settings.redis.startup_nodes).redis
