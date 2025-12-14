<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { Icon } from '@iconify/vue'

//api stuff
import { createClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { PdfService } from "../bibliophage/v1alpha2/pdf_connect.ts";
import { SearchPdfsRequest, Pdf, PdfListItem } from "../bibliophage/v1alpha2/pdf_pb.ts";
import { SortOrder } from "../bibliophage/v1alpha2/common_pb.ts";

// see https://connectrpc.com/docs/node/using-clients/#connect
const transport = createConnectTransport({
  baseUrl: "http://localhost:8000",  // TODO: make this configurable
});
const client = createClient(PdfService, transport);

const detectives = ref(
  [
    {name: "Justus Jonas", role: "Erster Detektiv"},
    {name: "Peter Shaw", role: "Zweiter Detektiv"},
    {name: "Bow Andrews", role: "Recherchen und Archiv"},
  ]
)

const pdfs = ref<PdfListItem[]>([])
const loading = ref(false)
const output = ref<string[]>([])

//TODO: make this actually send the Search request
//onBeforeMount(async () => {
  // send a search without  any filters and use that for our table of pdfs
//})  

// TODO: bend this around to handle  PDF searching
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

// TODO: bend this around to send a PDF search request
async function handleSearchSubmit() {
  loading.value = true;

  try {
    const request = buildSearchPdfsRequest();
    output.value.push("Searching for PDFs...");

    output.value.push("Sending Request...");
    const response = await client.searchPdfs(request);

    // Store the results
    pdfs.value = response.pdfs;
    output.value.push(`Success! Found ${response.totalCount} PDFs`);
    output.value.push(`Returned ${response.pdfs.length} results on page ${response.pageNumber}`);

  } catch (error) {
    output.value.push(`Error during PDF search: ${(error as Error).message}`);
  } finally {
    loading.value = false;
    output.value.push("");
  }
}


</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">Document List</h1>
    <p class="text-lg">Here is where we would like to have a searchable list of all documents</p>
  </div>
  
  <!-- Output Terminal -->
  <!--If something is in our list of output strings, display it here -->
  <!--<div v-if="output.length > 0" class="card bg-base-100 shadow-xl max-w-5xl mx-auto">-->
  <div class="card bg-base-100 shadow-xl max-w-5xl mx-auto">
    <div class="card-body">
      <h2 class="card-title">
        <Icon icon="heroicons:command-line" class="text-xl" />
        Output
      </h2>
      <div class="bg-base-200 rounded-lg p-4 font-mono text-sm">
        <pre v-for="(line, index) in output" :key="index" class="mb-1">{{ line }}</pre>
      </div>
    </div>
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

<details class="collapse bg-base-100 border-base-300 border">
      <summary class="collapse-title font-bold">PDFs</summary>
      <div class="collapse-content text-sm">
        <div class="overflow-x-auto">
          <table class="table table-s">
            <thead>
              <tr>
                <th>Index</th>
                <th>Name</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              <!--https://vuejs.org/guide/essentials/list-->
              <!--TODO: do we need this to be reactive? apparently, we can
              do something along those lines using the additional key= parameter
              https://vuejs.org/guide/essentials/list#maintaining-state-with-key -->
              <tr v-for="(item, index) in detectives" :key="index">
                <th>{{ index }}</th>
                <td>{{ item.name }}</td>
                <td>{{ item.role }}</td>
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