<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

//api stuff
import { createClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { LoadingService } from "../api/api_connect.ts";
import type { PdfLoadRequest } from "../api/api_pb.ts";

// TODO: We need to derive most of this from environment variables
// Form state
// ref() is a Vue function that returns an object with a single property .value
// basically a pointer. But the neat thing is that Vue tracks the value of this 
// object and does stuff in reaction to it changing (they call that "reactive")
// https://vuejs.org/api/reactivity-core.html#ref
// using the const keyword instead of var is us saying "we will always be storing the same
// pointer here, and no other", technically, var could work too, but then someone could reassign the ref
// and not just the ref's .value property
const serverAddress = ref('localhost')
const serverPort = ref(50051)
const pdfName = ref('')
const rpgSystem = ref('PATHFINDER_1E')
const publicationType = ref('BESTIARY')
const chunkSize = ref(600)
const chunkOverlap = ref(50)
// a ref to either a File or null, which we initialise to null
const pdfFile = ref<File | null>(null)
// if we are loading, we display a cute little animation
const loading = ref(false)
const output = ref<string[]>([])

// see https://connectrpc.com/docs/node/using-clients/#connect
const transport = createConnectTransport({
  baseUrl: `${serverAddress.value}:${serverPort.value}`,
});
const client = createClient(LoadingService, transport);

// if someone used our file input element to select a file
// - store that file object (which gives access to data AND metadata of that file) in  pdfFile.value
// https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    // in case the first file in the files property is undefined due to whatever reason, set the value to null
    // ?? works like || execpt that it returns the right side  if the left side is null or undefined 
    pdfFile.value = target.files[0] ?? null
    // a?.b means `a` might be undefined or null, but if it isn't, we would like to access `b` 
    // if b then happens do be undefined, `??` returns a string saying that instead
    const fileName = target.files[0]?.name ?? 'undefined'
    // regex replace all case variations of `.pdf` with an empty string
    pdfName.value = fileName.replace(/\.[pP][dD][fF]/, '')
  }
}

// async functions return a promise which other stuff
// can await, or use then(), finally() and other funny  Promise related functions on
// we don't do that though 
async function handleFormSubmit() {
  // returning settles the promise
  // if we do not explicitly return a value, we return `undefined`
  // in that case, the Promise is still considered settled
  if (!pdfFile.value) {
    return
  }

  // show cute loading animation
  loading.value = true
  output.value = []

  output.value.push(`Connecting to server at ${serverAddress.value}:${serverPort.value}...`)
  output.value.push(`File: ${pdfFile.value.name}`)
  output.value.push(`PDF Name: ${pdfName.value}`)
  output.value.push(`System: ${rpgSystem.value}`)
  output.value.push(`Type: ${publicationType.value}`)
  output.value.push('')
  

  try {
    // Prepare the RPC request
    const request: PdfLoadRequest = {
      pdfName: pdfName.value,
      // TODO: we will probably have to rework the whole RPG system idea, because  hardcoding them into the API seems silly
      pdfSystem: rpgSystem.value,
      publicationType: publicationType.value,
      // TODO: the api (and also the python server) currently does not handle files, and only uses their absolute path
      fileData: new Uint8Array(await pdfFile.value.arrayBuffer()),
    };

    // Make the Connect-RPC call (async)
    const response = await client.loadPDF(request);

    output.value.push("Upload successful!");
    output.value.push(JSON.stringify(response, null, 2));
  } catch (error) {
    // TODO: check if we are correctly handling timeouts
    output.value.push(`Error during upload: ${(error as Error).message}`);
  } finally {
    loading.value = false;
    output.value.push("");
  }
}

</script>

<template>
  <div class="max-w-7xl mx-auto">
    <h1 class="text-4xl font-bold mb-8">PDF Upload</h1>

    <!-- .prevent is an event modifier -->
    <!-- see https://vuejs.org/guide/essentials/event-handling.html#event-modifiers -->
    <!-- it's a short form for event.preventDefault() -->
    <!-- see https://developer.mozilla.org/en-US/docs/Web/API/Event/preventDefault -->
    <!-- preventDefault() prevents the default behaviour of an event -->
    <!-- that is because we are handling the response to the event ourselves with our event handler -->
    <!-- normally the submit event on a form would try to make a POST request-->
    <!-- with the entered values to a specified URL and reload the page-->
    <!-- see https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/submit_event-->
    <form @submit.prevent="handleFormSubmit">
      <!-- Card Grid Layout -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">

        <!-- Server Configuration -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title text-lg">
              <Icon icon="heroicons:server" class="text-xl" />
              Server Configuration
            </h2>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Server Address</span>
              </label>
              <input type="text" v-model="serverAddress" class="input input-bordered" />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Server Port</span>
              </label>
              <input type="number" v-model="serverPort" :min="1" :max="65535" class="input input-bordered" />
            </div>
          </div>
        </div>

        <!-- PDF File -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title text-lg">
              <Icon icon="heroicons:document" class="text-xl" />
              PDF File
            </h2>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Select PDF</span>
              </label>
              <!-- the @change="ABC" means, that our Vue code executes the handler ABC on change events-->>
              <!-- see https://vuejs.org/guide/essentials/event-handling.html -->
              <!-- handlers can also be inline functions -->
              <input type="file" accept=".pdf" @change="handleFileSelect" class="file-input file-input-bordered" />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">PDF Name</span>
              </label>
              <input type="text" v-model="pdfName" class="input input-bordered" />
            </div>
          </div>
        </div>

        <!-- Metadata -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title text-lg">
              <Icon icon="heroicons:tag" class="text-xl" />
              Metadata
            </h2>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">RPG System</span>
              </label>
              <select v-model="rpgSystem" class="select select-bordered">
                <option value="DND_35">D&D 3.5</option>
                <option value="PATHFINDER_1E">Pathfinder 1e</option>
                <option value="PATHFINDER_2E">Pathfinder 2e</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Publication Type</span>
              </label>
              <select v-model="publicationType" class="select select-bordered">
                <option value="CORE_RULEBOOK">Core Rulebook</option>
                <option value="BESTIARY">Bestiary</option>
                <option value="SUPPLEMENT">Supplement</option>
                <option value="ADVENTURE">Adventure</option>
                <option value="SETTING">Setting</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Chunking Parameters -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title text-lg">
              <Icon icon="heroicons:adjustments-horizontal" class="text-xl" />
              Chunking Parameters
            </h2>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Chunk Size (100-2000)</span>
              </label>
              <input type="number" v-model="chunkSize" :min="100" :max="2000" class="input input-bordered" />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">Chunk Overlap (0-500)</span>
              </label>
              <input type="number" v-model="chunkOverlap" :min="0" :max="500" class="input input-bordered" />
            </div>
          </div>
        </div>

      </div>

      <!-- Submit Button -->
      <div class="max-w-2xl mx-auto mb-6">
        <button
          type="submit"
          class="btn btn-accent btn-lg w-full gap-2"
          :disabled="!pdfFile || loading"
        >
          <Icon v-if="!loading" icon="heroicons:arrow-up-tray" class="text-xl" />
          <span v-if="loading" class="loading loading-spinner"></span>
          {{ !pdfFile ? 'Select a PDF first' : 'Load PDF' }}
        </button>
        <p v-if="!pdfFile" class="text-center text-sm mt-2 opacity-70">
          Please select a PDF file to upload
        </p>
      </div>

      <!-- Output Terminal -->
      <!--If something is in our list of output strings, display it here -->>
      <div v-if="output.length > 0" class="card bg-base-100 shadow-xl max-w-5xl mx-auto">
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

    </form>
  </div>
</template>
