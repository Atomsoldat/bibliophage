<script setup lang="ts">
import type { Client } from '@connectrpc/connect'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { onMounted, ref } from 'vue'

import { DocumentService } from '../bibliophage/v1alpha2/document_connect.ts'
import { Document, DocumentType, StoreDocumentRequest } from '../bibliophage/v1alpha2/document_pb.ts'
import TextEditorCard from '../components/TextEditorCard.vue'
import { useConfig } from '../composables/useConfig'

const { config, loadConfig } = useConfig()

// Client will be initialized after config loads
// see https://connectrpc.com/docs/node/using-clients/#connect
const client = ref<Client<typeof DocumentService> | null>(null)

// technically this is not necessary, because the editor just initialises itself with this
// string, but apparently we  can end up  with desynchronised variables if we don't override the value
// of a property with a default value in the child
// see the warning here
// https://vuejs.org/guide/components/v-model.html#under-the-hood
// besides, we will probably want to pass some string into an editor, e.g.  when editing an existing note
// so that is probably how we would do that
const editorDefaultContent = ref('<p>ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ<p>')
const editorContent = ref('Verschwindibus')

// Template ref to access the TextEditorCard component instance
const editorCardRef = ref<InstanceType<typeof TextEditorCard> | null>(null)

const documentName = ref('i-should-change-for-each-document')

onMounted(async () => {
  // Load configuration
  await loadConfig()

  // Create client with loaded config
  const transport = createConnectTransport({
    baseUrl: config.value.backendHost,
  })
  client.value = createClient(DocumentService, transport)
})

function buildDocumentStoreRequest(documentName: string, documentContent: string): StoreDocumentRequest {
  // Create the document object
  const document = new Document({
    name: documentName,
    content: documentContent,
    type: DocumentType.NOTE, // Default to NOTE type
    tags: [], // Empty tags for now
  })

  // Create the request with the document
  const req = new StoreDocumentRequest({
    document,
  })

  return req
}

// not part of the API... yet
// function buildDocumentUpdateRequest(id: Int, stringData: string): DocumentUpdateRequest {
//  const req = new DocumentUpdateRequest();
//  req.documentName = documentName.value;
//  req.id = 999;
//  req.content = stringData;
//
//  return req;
// }

// if the document is new, send a DocumentStoreRequest
// TODO: sed some kind of output / user feedback during this
async function handleDocumentSave() {
  if (!client.value) {
    console.error('Client not initialized. Configuration may not be loaded yet.')
    return
  }

  try {
    // TODO: if we are editing an existing doc, send a DocumentUpdateRequest
    const request = buildDocumentStoreRequest(documentName.value, editorContent.value)

    // TODO: do something with the response
    // const response = await client.loadPDF(request);
    await client.value.storeDocument(request)
  }
  catch (error) {
    // this should also do stuff
  }
  finally {
    // stuff
  }
}

async function handleDocumentAbort() {
  try {
    // Reset the editor to the default content
    editorCardRef.value?.resetEditor(editorDefaultContent.value)
  }
  catch (error) {
    // what could happen here, that we would  want to catch?
  }
  finally {
    // stuff
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4">
    <!-- mb for spacing underneath heading -->
    <h1 class="text-4xl font-bold mb-8">
      Journal
    </h1>

    <!-- TODO: Some kind of selector for notes -->
    <!-- Tree Structure and sortable/searchable by name, date, category, ... -->
    <!-- Drag and Drop Notes to establish hierarchies? Or is that too easy to mess up? Maybe have a button for that -->

    <div class="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-6 mb-6">
      <!-- v-model basically means -->
      <!-- "The child component gets passed this variable -->
      <!-- and when it modifies its copy, the parent copy is also modified" -->
      <!-- https://vuejs.org/guide/components/v-model -->
      <!-- for this to work, the child has to do some stuff as well, see -->
      <!-- https://vuejs.org/api/sfc-script-setup.html#definemodel -->
      <!-- directly putting an HTML string in here was annoying, hence variable -->
      <!-- multiple v-model:variable pairs can be passed -->
      <TextEditorCard
        ref="editorCardRef"
        v-model:content="editorContent"
        :title="documentName"
        icon="heroicons:document-text"
        @save="handleDocumentSave"
        @abort="handleDocumentAbort"
      />
    </div>
  </div>
</template>
