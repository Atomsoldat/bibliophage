<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { Icon } from '@iconify/vue'
import type { Client } from "@connectrpc/connect"

//api stuff
import { createClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { PdfService } from "../bibliophage/v1alpha2/pdf_connect.ts";
import { SearchPdfsRequest, Pdf, PdfListItem } from "../bibliophage/v1alpha2/pdf_pb.ts";
import { SortOrder } from "../bibliophage/v1alpha2/common_pb.ts";

// Configuration
import { useConfig } from "../composables/useConfig";
import { useAppConsole } from "../composables/useAppConsole";

const { config, loadConfig } = useConfig();
const { log } = useAppConsole();

// Client will be initialized after config loads
// see https://connectrpc.com/docs/node/using-clients/#connect
const client = ref<Client<typeof PdfService> | null>(null)

const detectives = ref(
  [
    {name: "Justus Jonas", role: "Erster Detektiv"},
    {name: "Peter Shaw", role: "Zweiter Detektiv"},
    {name: "Bow Andrews", role: "Recherchen und Archiv"},
  ]
)

const pdfs = ref<PdfListItem[]>([])
const loading = ref(false)

onBeforeMount(async () => {
  // Load configuration first
  await loadConfig()

  // Create client with loaded config
  const transport = createConnectTransport({
    baseUrl: config.value.backendHost,
  });
  client.value = createClient(PdfService, transport);

  // Send initial search to populate table
  handleSearchSubmit()
})  

function buildSearchPdfsRequest(): SearchPdfsRequest {

  // Create the request with hardcoded search parameters
  const req = new SearchPdfsRequest({
    titleQuery: "",      
    systemFilter: "PATHFINDER_1E",         
    typeFilter: "",           
    tagFilters: [],                        
    pageSize: 20,                          
    pageNumber: 0,                        
    sortOrder: SortOrder.NAME_ASC,        
  });

  return req;
}

async function handleSearchSubmit() {
  if (!client.value) {
    log("Error: Client not initialized. Configuration may not be loaded yet.", "error");
    return;
  }

  loading.value = true;

  try {
    const request = buildSearchPdfsRequest();
    log("Searching for PDFs...", "info");

    const response = await client.value.searchPdfs(request);

    // Store the results
    pdfs.value = response.pdfs;
    log(`Success! Found ${response.totalCount} PDFs`, "success");
    log(`Returned ${response.pdfs.length} results on page ${response.pageNumber}`, "info");

  } catch (error) {
    log(`Error during PDF search: ${(error as Error).message}`, "error");
  } finally {
    loading.value = false;
  }
}


</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">Document List</h1>
    <p class="text-lg">Here is where we would like to have a searchable list of all documents</p>
  </div>

<form @submit.prevent="handleSearchSubmit">

  <button
    type="search"
    class="btn btn-accent btn-lg w-full gap-2"
    :disabled="loading"
  >
    <Icon v-if="!loading" icon="game-icons:magnifying-glass" class="text-xl" />
    <span v-if="loading" class="loading loading-spinner"></span>
    Search
  </button>
</form>

<!-- TODO: I think this should be open by default, at least until we have more document types -->
<!-- TODO: Make Table Columns adjustable (show or hide, possibly width?)-->
<details class="collapse bg-base-100 border-base-300 border">
      <summary class="collapse-title font-bold">PDFs</summary>
      <div class="collapse-content text-sm">
        <div class="overflow-x-auto">
          <table class="table table-s">
            <thead>
              <tr>
                <th>Index</th>
                <th>Name</th>
                <th>ID</th>
                <th>System</th>
                <th>Type</th>
                <th>Page Count</th>
                <th>Origin Path</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Size</th>
                <th>Chunk Count</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              <!-- https://vuejs.org/guide/essentials/list -->
              <!-- https://vuejs.org/guide/essentials/list#maintaining-state-with-key -->
              <tr v-for="(item, index) in pdfs" :key="index">
                <th>{{ index }}</th>
                <td>{{ item.name }}</td>
                <td>{{ item.id }}</td>
                <td>{{ item.system }}</td>
                <td>{{ item.type }}</td>
                <td>{{ item.pageCount }}</td>
                <td>{{ item.originPath }}</td>
                <!-- TODO: use human readable units-->
                <td>{{ item.createdAt }}</td>
                <td>{{ item.updatedAt }}</td>
                <!-- TODO: use human readable units-->
                <td>{{ item.fileSize }}</td>
                <td>{{ item.chunkCount }}</td>
                <td>{{ item.tags }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <th></th>
                <th>Name</th>
                <th>Role</th>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </details>
</template>