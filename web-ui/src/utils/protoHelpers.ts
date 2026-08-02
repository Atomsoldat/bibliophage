import type { Tag } from '../bibliophage/v1alpha3/tag_pb.ts'
import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { DocumentFilter, DocumentListItem, SearchDocumentsRequest } from '../bibliophage/v1alpha3/document_pb.ts'
import { LoadPdfRequest, Pdf } from '../bibliophage/v1alpha3/pdf_pb.ts'

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

export interface LoadPdfParams {
  name: string
  tags: Tag[]
  fileData: Uint8Array<ArrayBuffer>
}

export function buildLoadPdfRequest(params: LoadPdfParams): LoadPdfRequest {
  const pdf = new Pdf({
    name: params.name,
    tags: params.tags,
  })

  return new LoadPdfRequest({
    pdf,
    fileData: params.fileData,
  })
}
