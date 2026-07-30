import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { DocumentFilter, DocumentListItem, SearchDocumentsRequest } from '../bibliophage/v1alpha3/document_pb.ts'

// Re-export protobuf types for use by consumers
export { DocumentListItem, SortOrder }

export interface SearchDocumentsParams {
  nameQuery: string
  pageSize: number
  pageNumber: number
  sortOrder: SortOrder
}

export function buildSearchDocumentsRequest(params: SearchDocumentsParams): SearchDocumentsRequest {
  const filter = new DocumentFilter({
    nameQuery: params.nameQuery,
    tagFilters: [], // TODO: Tag filtering not implemented yet
  })

  return new SearchDocumentsRequest({
    filter,
    pageSize: params.pageSize,
    pageNumber: params.pageNumber,
    sortOrder: params.sortOrder,
  })
}
