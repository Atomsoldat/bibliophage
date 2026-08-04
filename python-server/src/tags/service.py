import logging

import bibliophage.v1alpha3.embedding_pb2 as embedding_api
import bibliophage.v1alpha3.tag_pb2 as tag_api
from db.postgres_db import get_postgres_db
from proto_converters import (
    metadata_proto_to_dict,
    row_to_proto_tag,
)

logger = logging.getLogger(__name__)



class TagServiceImplementation:
    def __init__(self):
        """Initialise the tag service with database repository."""
        self.db = get_postgres_db()
        logger.info("Tag service initialised with database repository")

    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_tag(
        self,
        request: tag_api.StoreTagRequest,
        ctx,
    ) -> tag_api.StoreTagResponse:
        logger.info(
            f"Received StoreTagRequest for tag: {request.tag.name}",
        )

        try:
            response = await self.db.store_tag(
                name=request.tag.name,
                colour=request.tag.colour,
            )
        except ValueError as e:
            return tag_api.StoreTagResponse(
                success=False,
                message=str(e),
            )

        ## why?
        # Create response with stored tag metadata
        stored_tag = tag_api.Tag()
        stored_tag.CopyFrom(request.tag)
        stored_tag.id = response["tag_id"]
        stored_tag.name = response["name"]
        stored_tag.colour = response["colour"]

        return tag_api.StoreTagResponse(
            success=True,
            message=f"Tag '{stored_tag.name}' stored successfully",
            tag=stored_tag,
        )

    async def delete_tag(
        self,
        request: tag_api.DeleteTagRequest,
        ctx,
    ) -> tag_api.DeleteTagResponse:
        logger.info(f"Received DeleteTagRequest for ID: {request.id}")

        # Delete tag from database
        deleted = await self.db.delete_tag(request.id)

        if not deleted:
            return tag_api.DeleteTagResponse(
                success=False,
                message=f"Tag with ID {request.id} could not be deleted",
            )

        return tag_api.DeleteTagResponse(
            success=True,
            message=f"Tag with ID {request.id} deleted successfully",
        )

    async def rename_tag(
        self,
        request: tag_api.RenameTagRequest,
        ctx,
    ) -> tag_api.RenameTagResponse:
        logger.info(f"Received RenameTagRequest for ID: {request.id}")

        renamed = await self.db.rename_tag(request.id, request.name)

        if not renamed:
            # TODO: I think returning proper SQL error codes / messages as part of the message
            # would be the good thing to do here, and in other cases like this
            return tag_api.RenameTagResponse(
                success=False,
                message=f"Tag with ID {request.id} could not be renamed to {request.name}",
            )
        tag=tag_api.Tag()
        tag.name=renamed["name"]
        tag.id=renamed["id"]

        return tag_api.RenameTagResponse(
            success=True,
            message=f"Tag with ID {request.id} renamed to {request.name} successfully",
            tag=tag
        )

    async def update_tag_colour(
        self,
        request: tag_api.UpdateTagColourRequest,
        ctx,
    ) -> tag_api.UpdateTagColourResponse:
        logger.info(f"Received UpdateTagColourRequest for ID: {request.id}")

        upd00t = await self.db.recolour_tag(request.id, request.colour)

        if not upd00t:
            # TODO: I think returning proper SQL error codes / messages as part of the message
            # would be the good thing to do here, and in other cases like this
            return tag_api.UpdateTagColourResponse(
                success=False,
                message=f"Tag with ID {request.id} could not be recoloured to {request.colour}",
            )
        # TODO: we must make the SQL return the tag with its name, so that this does not have to
        # go fetch it
        tag=tag_api.Tag()
        tag.name=upd00t["name"]
        tag.id=upd00t["id"]
        tag.colour=upd00t["colour"]

        return tag_api.UpdateTagColourResponse(
            success=True,
            message=f"Tag with ID {request.id} recoloured to {request.colour} successfully",
            tag=tag
        )

    async def store_tag_value(
        self,
        request: tag_api.StoreTagValueRequest,
        ctx,
    ) -> tag_api.StoreTagValueResponse:
        logger.info(
            f"Received StoreTagValueRequest for tag {request.id} value: {request.tag_value.value}",
        )

        try:
            response = await self.db.store_tag_value(
                tag_id=request.id,
                value=request.tag_value.value,
            )
        except ValueError as e:
            return tag_api.StoreTagValueResponse(
                success=False,
                message=str(e),
            )

        # TODO: make sure this returns the required data
        # otherwise, we need to fetch it
        stored_tag_value = tag_api.TagValue()
        stored_tag_value.id = response["tag_value_id"]
        stored_tag_value.value = response["name"]

        return tag_api.StoreTagValueResponse(
            success=True,
            message=f"Tag value '{stored_tag_value.value}' with id {stored_tag_value.id} stored successfully for tag with id {request.id}",
            tag_value=stored_tag_value,
        )

    async def delete_tag_value(
        self,
        request: tag_api.DeleteTagValueRequest,
        ctx,
    ) -> tag_api.DeleteTagResponse:
        logger.info(f"Received DeleteTagValueRequest for ID: {request.id}")

        # Delete tag from database
        deleted = await self.db.delete_tag_value(request.id)

        if not deleted:
            return tag_api.DeleteTagResponse(
                success=False,
                message=f"Tag value with ID {request.id} could not be deleted",
            )

        return tag_api.DeleteTagResponse(
            success=True,
            message=f"Tag value with ID {request.id} deleted successfully",
        )

    async def rename_tag_value(
        self,
        request: tag_api.RenameTagValueRequest,
        ctx,
    ) -> tag_api.RenameTagValueResponse:
        logger.info(f"Received RenameTagValueRequest for ID: {request.id}")

        renamed = await self.db.rename_tag_value(request.id, request.name)

        if not renamed:
            # TODO: I think returning proper SQL error codes / messages as part of the message
            # would be the good thing to do here, and in other cases like this
            return tag_api.RenameTagValueResponse(
                success=False,
                message=f"Tag value with ID {request.id} could not be renamed to {request.name}",
            )
        tag_value=tag_api.Tag()
        tag_value.name=renamed["name"]
        tag_value.id=renamed["id"]

        return tag_api.RenameTagValueResponse(
            success=True,
            message=f"Tag value with ID {request.id} renamed to {request.name} successfully",
            tag_value=tag_value
        )

    async def get_tag(
        self,
        request: tag_api.GetTagRequest,
        ctx,
    ) -> tag_api.GetTagResponse:
        logger.info(f"Received GetTagRequest for ID: {request.id}")

        count_docs = bool(request.count_docs)
        count_values = bool(request.count_values)

        # Retrieve tag from database
        tag_data = await self.db.get_tag_by_id(request.id, count_docs, count_values)

        if tag_data is None:
            return tag_api.GetTagResponse(
                success=False,
                message=f"Tag with ID {request.id} could not be retrieved",
            )

        tag = row_to_proto_tag(tag_data)

        return tag_api.GetTagResponse(
            success=True,
            message=f"Tag '{tag.name}' retrieved successfully",
            tag=tag,
        )

    async def get_tags(
        self,
        request: tag_api.GetTagsRequest,
        ctx,
    ) -> tag_api.GetTagsResponse:
        logger.info(f"Received GetTagsRequest for substring: {request.name_filter}")

        count_docs = bool(request.count_docs)
        count_values = bool(request.count_values)

        # Retrieve tags from database
        tags_data = await self.db.get_tags_by_name(request.name_filter, count_docs, count_values)

        if tags_data is None:
            return tag_api.GetTagsResponse(
                success=False,
                message=f"Tags matching substring {request.name_filter} could not be retrieved",
            )

        tags = [row_to_proto_tag(row) for row in tags_data]

        return tag_api.GetTagsResponse(
            success=True,
            message=f"{len(tags)} tags retrieved successfully",
            tags=tags,
        )
