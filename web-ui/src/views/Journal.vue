i<script setup lang="ts">
import { ref } from 'vue'

import TextEditor from '../components/TextEditor.vue';
import BaseCard from '../components/BaseCard.vue';

// technically this is not necessary, because the editor just initialises itself with this
// string, but apparently we  can end up  with desynchronised variables if we don't override the value
// of a property with a default value in the child
// see the warning here
// https://vuejs.org/guide/components/v-model.html#under-the-hood
// besides, we will probably want to pass some string into an editor, e.g.  when editing an existing note
// so that is probably how we would do that
const editorDefaultContent = ref('<p>ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ<p>')

    

</script>

<template>
  <div class="max-w-max mx-auto">
    <!-- mb for spacing underneath heading-->
    <h1 class="text-4xl font-bold mb-8">Journal</h1>
    
    <!--TODO: Some kind of selector for notes-->
    <!-- Tree Structure and sortable/searchable by name, date, category, ... -->
    <!-- Drag and Drop Notes to establish hierarchies? Or is that too easy to mess up? Maybe have a button for that-->


    
    <div class="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-6 mb-6">
      <!-- v-model basically means -->
      <!--"The child component gets passed this variable-->
      <!-- and when it modifies its copy, the parent copy is also modified" -->
      <!-- https://vuejs.org/guide/components/v-model -->
      <!-- for this to work, the child has to do some stuff as well, see-->
      <!-- https://vuejs.org/api/sfc-script-setup.html#definemodel-->
      <!-- directly putting an HTML string in here was annoying, hence variable -->
      <!-- multiple v-model:variable pairs can be passed-->
      <!-- TODO: make the tile of the editor reflect the Name of the Document being edited -->
      <!-- TODO: Save / Cancel Button-->
      <BaseCard title="Dynamic Title" icon="heroicons:document-text"
      class="col-span-1 md:col-span-2 xl:col-span-3">
        <text-editor v-model:defaultContent="editorDefaultContent"/>

        <div class="flex center-safe justify-between">
          <!--TODO: make these buttons do something-->
          <button
            type="submit"
            class="btn btn-primary btn-lg w-fit gap-2 justify-items-start">
            <p>Save</p>
          </button>
          <button
            type="reset"
            class="btn btn-error btn-lg w-fit gap-2 justify-items-end">
            <p>Abort</p>
          </button>
        </div>
      </BaseCard>
    </div>
  </div>
</template>