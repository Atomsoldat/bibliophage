import logging

import bibliophage.v1alpha3.canon_pb2 as canon_api
from db.postgres_db import get_postgres_db
from proto_converters import (
    datetime_to_proto_ts,
    row_to_proto_document,
)

logger = logging.getLogger(__name__)


class CanonServiceImplementation:
    def __init__(self):
        """Initialize the canon service with database repository."""
        self.db = get_postgres_db()
        logger.info("Canon service initialized with database repository")


    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_canon(
        self,
        request: canon_api.StoreCanonRequest,
        ctx,
    ) -> canon_api.StoreCanonResponse:
        logger.info(
            f"Received StoreCanonRequest for canon: {request.canon.name}",
        )


        # Convert protobuf tags to dict format for database storage
        tags = []
        for tag in request.canon.tags:
            tags.append({"name": tag.name, "values": list(tag.values)})

        try:
            # TODO: implement this subroutine in the DB layer
            response = await self.db.store_canon(
                name=request.canon.name,
                tags=tags,
            )
        except ValueError as e:
            return canon_api.StoreCanonResponse(
                success=False,
                message=str(e),
            )



        # Create response with stored canon metadata
        stored_canon = canon_api.Canon()
        stored_canon.CopyFrom(request.canon)
        # TODO: make sure our DB layer returns this as expected
        stored_canon.id = response["canon_id"]

        # Set timestamps — must use FromDatetime, not direct assignment
        created_ts = datetime_to_proto_ts(response["created_at"])
        stored_canon.created_at.CopyFrom(created_ts)
        stored_canon.updated_at.CopyFrom(created_ts)

        return canon_api.StoreCanonResponse(
            success=True,
            message=f"Canon '{stored_canon.name}' stored successfully",
            canon=stored_canon,
        )


    async def get_canon(
        self,
        request: canon_api.GetCanonRequest,
        ctx,
    ) -> canon_api.GetCanonResponse:
        logger.info(f"Received GetCanonRequest for ID: {request.id}")

        canon_data = await self.db.get_canon_by_id(request.id)

        if canon_data is None:
            return canon_api.GetCanonResponse(
                success=False,
                message=f"Canon with ID {request.id} not found",
            )

        canon = row_to_proto_document(canon_data)

        return canon_api.GetCanonResponse(
            success=True,
            message=f"Canon '{canon.name}' retrieved successfully",
            canon=canon,
        )


    async def update_canon(
        self,
        request: canon_api.UpdateCanonRequest,
        ctx,
    ) -> canon_api.UpdateCanonResponse:
        """Update a canon by ID. Full replace strategy"""
        logger.info(f"Received UpdateCanonRequest for ID: {request.canon.id}")

        if not request.canon.id:
            return canon_api.UpdateCanonResponse(
                success=False,
                message="Canon ID is required",
            )

        # Convert protobuf tags to dict format for database storage
        tags = [
            {"name": tag.name, "values": list(tag.values)}
            for tag in request.canon.tags
        ]

        try:
            # TODO: implement this subroutine
            result = await self.db.update_canon(
                canon_id=request.canon.id,
                name=request.canon.name,
                tags=tags,
            )
        except ValueError as e:
            return canon_api.UpdateCanonResponse(
                success=False,
                message=str(e),
            )

        if result is None:
            return canon_api.UpdateCanonResponse(
                success=False,
                message="Canon not found",
            )

        # TODO: does this make sense?
        # Re-fetch the full canon so db-computed fields are accurate
        # TODO: implement
        canon_data = await self.db.get_canon_by_id(request.canon.id)
        proto_canon = row_to_proto_document(canon_data)

        return canon_api.UpdateCanonResponse(
            success=True,
            message="Canon updated successfully",
            canon=proto_canon,
        )


    ############################ REWRITE ##################################
    async def search_canons(
        self,
        request: canon_api.SearchCanonsRequest,
        ctx,
    ) -> canon_api.SearchCanonsResponse:
        logger.info("Received SearchCanonsRequest")

        # Extract filter parameters if filter is provided
        name_query = None
        tag_filters = None

        if request.HasField("filter"):
            # Extract search parameters from filter
            name_query = (
                request.filter.name_query
                if request.filter.HasField("name_query")
                else None
            )

            # Extract tag filters (must match ALL)
            if request.filter.tag_filters:
                tag_filters = []
                for tag_filter in request.filter.tag_filters:
                    tag_filters.append(
                        {
                            "name": tag_filter.name,
                            "value": tag_filter.value,
                        },
                    )

        # Set page size with a reasonable default
        page_size = request.page_size if request.page_size > 0 else 50
        page_number = max(request.page_number, 0)

        # Call database search method
        # TODO: implement
        canons, total_count = await self.db.search_canons(
            name_query=name_query,
            tag_filters=tag_filters,
            page_size=page_size,
            page_number=page_number,
        )

        # Calculate if there are more results
        has_more = (page_number + 1) * page_size < total_count
        return canon_api.SearchCanonsResponse(
            success=True,
            message=f"Found {total_count} canon(s)",
            matches=canons,
            total_count=total_count,
            page_number=page_number,
            has_more=has_more,
        )

    async def delete_canon(
        self,
        request: canon_api.DeleteCanonRequest,
        ctx,
    ) -> canon_api.DeleteResponse:
        logger.info(f"Received DeleteCanonRequest for ID: {request.id}")

        # Delete canon from database
        # TODO: implement
        deleted = await self.db.delete_canon(request.id)

        if not deleted:
            return canon_api.DeleteCanonResponse(
                success=False,
                message=f"Canon with ID {request.id} could not be deleted",
            )

        return canon_api.DeleteCanonResponse(
            success=True,
            message=f"Canon with ID {request.id} deleted successfully",
        )
