import { describe, expect, it } from 'vitest'
import { Tag } from '../bibliophage/v1alpha3/tag_pb'
import { buildLoadPdfRequest } from './protoHelpers.ts'

describe('buildLoadPdfRequest', () => {
  it('carries the given name, tags and file data onto the request', () => {
    const tags = [new Tag({ id: 'tag-genre', name: 'genre' })]
    const fileData = new Uint8Array([1, 2, 3])

    const request = buildLoadPdfRequest({ name: 'Monster Manual', tags, fileData })

    expect(request.pdf?.name).toBe('Monster Manual')
    expect(request.pdf?.tags).toEqual(tags)
    expect(request.fileData).toEqual(fileData)
  })

  it('defaults to no tags', () => {
    const request = buildLoadPdfRequest({ name: 'Monster Manual', tags: [], fileData: new Uint8Array() })

    expect(request.pdf?.tags).toEqual([])
  })
})
