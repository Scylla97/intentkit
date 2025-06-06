import logging
from typing import Optional, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import TwitterUser, get_twitter_client

from .base import TwitterBaseTool

logger = logging.getLogger(__name__)

PROMPT = "Get a Twitter user's information by their username. Returns detailed user information including profile data, metrics, and verification status."


class TwitterGetUserByUsernameInput(BaseModel):
    """Input for TwitterGetUserByUsername tool."""

    username: str = Field(description="The Twitter username to lookup")


class TwitterGetUserByUsername(TwitterBaseTool):
    """Tool for getting a Twitter user by their username.

    This tool uses the Twitter API v2 to retrieve user information by username.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_get_user_by_username"
    description: str = PROMPT
    args_schema: Type[BaseModel] = TwitterGetUserByUsernameInput

    async def _arun(
        self, username: str, config: RunnableConfig, **kwargs
    ) -> Optional[TwitterUser]:
        """Async implementation of the tool to get a user by username.

        Args:
            username (str): The Twitter username to lookup.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            Optional[TwitterUser]: The Twitter user information if found, None otherwise.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            context = self.context_from_config(config)
            twitter = get_twitter_client(
                agent_id=context.agent.id,
                skill_store=self.skill_store,
                config=context.config,
            )

            # Check rate limit only when not using OAuth
            if not twitter.use_key:
                await self.check_rate_limit(
                    context.agent.id, max_requests=3, interval=60 * 24
                )

            client = await twitter.get_client()

            user_data = await client.get_user(
                username=username,
                user_auth=twitter.use_key,
                user_fields=[
                    "created_at",
                    "description",
                    "entities",
                    "connection_status",
                    "id",
                    "location",
                    "name",
                    "pinned_tweet_id",
                    "profile_image_url",
                    "protected",
                    "public_metrics",
                    "url",
                    "username",
                    "verified",
                    "verified_type",
                    "withheld",
                ],
            )

            return user_data

        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
