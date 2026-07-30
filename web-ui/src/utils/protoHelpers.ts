import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { DocumentFilter, DocumentListItem, DocumentType, SearchDocumentsRequest } from '../bibliophage/v1alpha3/document_pb.ts'

// Re-export protobuf types for use by consumers
export { DocumentListItem, DocumentType, SortOrder }

/**
 * Returns all DocumentType enum values.
 * Useful for initialising filters with all types enabled.
 */
export function getAllDocumentTypes(): DocumentType[] {
  return Object.values(DocumentType).filter(v => typeof v === 'number') as DocumentType[]
}

export interface SearchDocumentsParams {
  nameQuery: string
  typeFilters: DocumentType[]
  pageSize: number
  pageNumber: number
  sortOrder: SortOrder
}

export function buildSearchDocumentsRequest(params: SearchDocumentsParams): SearchDocumentsRequest {
  const filter = new DocumentFilter({
    nameQuery: params.nameQuery,
    tagFilters: [], // TODO: Tag filtering not implemented yet
    typeFilters: params.typeFilters,
  })

  return new SearchDocumentsRequest({
    filter,
    pageSize: params.pageSize,
    pageNumber: params.pageNumber,
    sortOrder: params.sortOrder,
  })
}
